"""
Async image downloader with retry logic.

Downloads images in parallel using aiohttp for speed, with
exponential-backoff retries for transient network errors.
"""

from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import aiohttp

# Sensible defaults
MAX_CONCURRENT = 8          # Parallel download limit
RETRY_ATTEMPTS = 3          # Retries per image
RETRY_BASE_DELAY = 1.0      # Seconds before first retry (doubles each time)
DOWNLOAD_TIMEOUT = 15        # Per-image timeout in seconds


@dataclass
class DownloadResult:
    """Outcome of a single image download."""

    url: str
    path: Path | None       # None if the download failed
    success: bool
    error: str | None = None


def _sanitize_filename(name: str, max_len: int = 120) -> str:
    """Strip problematic characters from a filename."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = re.sub(r"_+", "_", name).strip("_. ")
    return name[:max_len] if name else "image"


def _extension_from_content_type(content_type: str) -> str:
    """Map a Content-Type header to a file extension."""
    mapping = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/bmp": ".bmp",
        "image/svg+xml": ".svg",
    }
    # Content-Type may contain params like "; charset=utf-8"
    mime = content_type.split(";")[0].strip().lower()
    return mapping.get(mime, ".jpg")


async def _download_one(
    session: aiohttp.ClientSession,
    url: str,
    dest_dir: Path,
    index: int,
    on_progress: Callable[[str, bool], None] | None = None,
) -> DownloadResult:
    """
    Download a single image with retries.

    Args:
        session:     Shared aiohttp session.
        url:         Direct image URL.
        dest_dir:    Folder to save into.
        index:       Numeric index (used for filename prefix).
        on_progress: Optional callback(url, success) fired on completion.
    """
    last_error = ""

    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            timeout = aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT)
            async with session.get(url, timeout=timeout) as resp:
                if resp.status != 200:
                    last_error = f"HTTP {resp.status}"
                    # Don't retry client errors (4xx)
                    if 400 <= resp.status < 500:
                        break
                    await asyncio.sleep(RETRY_BASE_DELAY * (2 ** (attempt - 1)))
                    continue

                content_type = resp.headers.get("Content-Type", "image/jpeg")

                # Skip non-image responses
                if not content_type.startswith("image"):
                    last_error = f"Not an image: {content_type}"
                    break

                ext = _extension_from_content_type(content_type)
                # Build a filename from the URL's last path segment
                url_stem = url.rsplit("/", 1)[-1].split("?")[0]
                base = _sanitize_filename(
                    os.path.splitext(url_stem)[0] or f"image_{index}"
                )
                filename = f"{index:03d}_{base}{ext}"
                filepath = dest_dir / filename

                data = await resp.read()
                filepath.write_bytes(data)

                if on_progress:
                    on_progress(url, True)

                return DownloadResult(url=url, path=filepath, success=True)

        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < RETRY_ATTEMPTS:
                await asyncio.sleep(RETRY_BASE_DELAY * (2 ** (attempt - 1)))

    # All retries exhausted
    if on_progress:
        on_progress(url, False)

    return DownloadResult(url=url, path=None, success=False, error=last_error)


async def download_images(
    urls: list[str],
    dest_dir: Path,
    on_progress: Callable[[str, bool], None] | None = None,
) -> list[DownloadResult]:
    """
    Download many images concurrently.

    Args:
        urls:        List of direct image URLs.
        dest_dir:    Target folder (created if missing).
        on_progress: Optional per-image callback(url, success).

    Returns:
        A list of DownloadResult for every URL.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async def _bounded(idx: int, url: str) -> DownloadResult:
        async with semaphore:
            return await _download_one(
                session, url, dest_dir, idx, on_progress
            )

    connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT, ssl=False)
    async with aiohttp.ClientSession(
        connector=connector,
        headers={"User-Agent": "PixelSearch/1.0"},
    ) as session:
        tasks = [_bounded(i, u) for i, u in enumerate(urls, start=1)]
        return await asyncio.gather(*tasks)
