"""
Image search scraper using DuckDuckGo.

Uses the duckduckgo-search library which scrapes DuckDuckGo's image
search results — no API key or payment required.
"""

from __future__ import annotations

from dataclasses import dataclass

from duckduckgo_search import DDGS


@dataclass(frozen=True)
class ImageResult:
    """A single image search result."""

    title: str
    url: str        # Direct URL to the image file
    source: str     # Page where the image was found
    width: int
    height: int


def search_images(
    query: str,
    max_results: int = 20,
    safe_search: str = "moderate",
) -> list[ImageResult]:
    """
    Search DuckDuckGo for images matching *query*.

    Args:
        query:       The search term.
        max_results: Maximum number of image results to return.
        safe_search: Safety level — "on", "moderate", or "off".

    Returns:
        A list of ImageResult objects with direct image URLs.
    """
    with DDGS() as ddgs:
        raw_results = ddgs.images(
            keywords=query,
            max_results=max_results,
            safesearch=safe_search,
        )

    results: list[ImageResult] = []
    for item in raw_results:
        results.append(
            ImageResult(
                title=item.get("title", "Untitled"),
                url=item.get("image", ""),
                source=item.get("source", ""),
                width=item.get("width", 0),
                height=item.get("height", 0),
            )
        )

    return results
