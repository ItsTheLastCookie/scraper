"""
Retro-themed terminal user interface built with Rich.

Provides the interactive search prompt, progress display,
result table, and ASCII thumbnail previews.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
)
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from . import __version__
from .ascii_art import image_to_ascii
from .downloader import DownloadResult, download_images
from .scraper import ImageResult, search_images

# ── Retro colour theme ──────────────────────────────────────────────
PIXEL_THEME = Theme(
    {
        "title": "bold bright_green",
        "border": "bright_green",
        "prompt": "bold bright_cyan",
        "info": "bright_yellow",
        "success": "bold bright_green",
        "error": "bold bright_red",
        "muted": "dim white",
        "accent": "bright_magenta",
    }
)

# ── ASCII banner ─────────────────────────────────────────────────────
BANNER = r"""
[title]
 ██████╗ ██╗██╗  ██╗███████╗██╗     ███████╗███████╗ █████╗ ██████╗  ██████╗██╗  ██╗
 ██╔══██╗██║╚██╗██╔╝██╔════╝██║     ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██║  ██║
 ██████╔╝██║ ╚███╔╝ █████╗  ██║     ███████╗█████╗  ███████║██████╔╝██║     ███████║
 ██╔═══╝ ██║ ██╔██╗ ██╔══╝  ██║     ╚════██║██╔══╝  ██╔══██║██╔══██╗██║     ██╔══██║
 ██║     ██║██╔╝ ██╗███████╗███████╗███████║███████╗██║  ██║██║  ██║╚██████╗██║  ██║
 ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
[/title]
[muted]               ░▒▓  Terminal Image Search  v{version}  ▓▒░[/muted]
"""


def _sanitize_folder_name(query: str) -> str:
    """Turn a search query into a safe directory name."""
    name = re.sub(r"[^\w\s-]", "", query.lower())
    return re.sub(r"[\s]+", "_", name).strip("_") or "images"


class PixelSearchTUI:
    """Interactive terminal interface for PixelSearch."""

    def __init__(self) -> None:
        self.console = Console(theme=PIXEL_THEME)

    # ── Display helpers ──────────────────────────────────────────────

    def show_banner(self) -> None:
        """Print the startup ASCII banner."""
        self.console.print(BANNER.format(version=__version__))

    def show_divider(self) -> None:
        self.console.rule(style="border")

    def prompt_query(self) -> str:
        """Ask the user for a search query.  Returns empty string to quit."""
        self.console.print()
        self.console.print(
            "[prompt]>>>[/prompt] Enter search query "
            "([muted]or 'q' to quit[/muted]): ",
            end="",
        )
        query = input().strip()
        if query.lower() in ("q", "quit", "exit"):
            return ""
        return query

    def prompt_max_results(self) -> int:
        """Ask how many images to fetch."""
        self.console.print(
            "[prompt]>>>[/prompt] How many images? "
            "([muted]default 10, max 1000[/muted]): ",
            end="",
        )
        raw = input().strip()
        try:
            n = int(raw)
            return max(1, min(n, 1000))
        except ValueError:
            return 10

    # ── Search phase ─────────────────────────────────────────────────

    def run_search(self, query: str, max_results: int) -> list[ImageResult]:
        """Execute the image search with a spinner."""
        self.console.print()
        with self.console.status(
            f"[info]Searching DuckDuckGo for '[accent]{query}[/accent]'…[/info]",
            spinner="dots",
        ):
            results = search_images(query, max_results=max_results)

        self.console.print(
            f"  [success]✔[/success] Found [accent]{len(results)}[/accent] "
            f"image results."
        )
        return results

    # ── Results table ────────────────────────────────────────────────

    def show_results_table(self, results: list[ImageResult]) -> None:
        """Display a numbered table of image results."""
        table = Table(
            title="[title]▸ Search Results[/title]",
            border_style="border",
            show_lines=True,
            padding=(0, 1),
        )
        table.add_column("#", style="accent", justify="right", width=4)
        table.add_column("Title", style="info", max_width=40, no_wrap=True)
        table.add_column("Size", style="muted", justify="center", width=12)
        table.add_column("URL", style="muted", max_width=50, no_wrap=True)

        for i, r in enumerate(results, 1):
            size = f"{r.width}×{r.height}" if r.width and r.height else "—"
            table.add_row(str(i), r.title[:40], size, r.url[:50])

        self.console.print()
        self.console.print(table)

    # ── Download phase ───────────────────────────────────────────────

    def run_downloads(
        self,
        urls: list[str],
        dest_dir: Path,
    ) -> list[DownloadResult]:
        """Download images with a live progress bar."""
        self.console.print()
        self.console.print(
            f"  [info]Downloading to:[/info] [accent]{dest_dir}[/accent]"
        )

        progress = Progress(
            SpinnerColumn("dots"),
            TextColumn("[info]{task.description}[/info]"),
            BarColumn(bar_width=30, style="border", complete_style="success"),
            MofNCompleteColumn(),
            console=self.console,
        )

        results: list[DownloadResult] = []

        with progress:
            task_id = progress.add_task("Downloading images…", total=len(urls))

            def on_progress(url: str, success: bool) -> None:
                progress.advance(task_id)

            # Run the async downloader inside a new event loop
            results = asyncio.run(
                download_images(urls, dest_dir, on_progress=on_progress)
            )

        ok = sum(1 for r in results if r.success)
        fail = len(results) - ok
        self.console.print(
            f"  [success]✔ {ok} downloaded[/success]"
            + (f"  [error]✘ {fail} failed[/error]" if fail else "")
        )
        return results

    # ── ASCII previews ───────────────────────────────────────────────

    def show_ascii_previews(self, results: list[DownloadResult]) -> None:
        """Render ASCII thumbnails for each successfully downloaded image."""
        self.console.print()
        self.console.print("[title]▸ ASCII Previews[/title]")
        self.show_divider()

        shown = 0
        for r in results:
            if not r.success or r.path is None:
                continue

            art = image_to_ascii(r.path, width=60)
            if "(preview unavailable)" in art:
                continue

            panel = Panel(
                Text(art, style="bright_green"),
                title=f"[accent]{r.path.name}[/accent]",
                border_style="border",
                padding=(0, 1),
            )
            self.console.print(panel)
            shown += 1

            # Only preview the first few to avoid flooding the terminal
            if shown >= 5:
                remaining = sum(
                    1 for x in results if x.success and x.path is not None
                ) - shown
                if remaining > 0:
                    self.console.print(
                        f"  [muted]…and {remaining} more saved to disk.[/muted]"
                    )
                break

    # ── Summary ──────────────────────────────────────────────────────

    def show_summary(self, dest_dir: Path, results: list[DownloadResult]) -> None:
        """Print a final summary panel."""
        ok = sum(1 for r in results if r.success)
        files = [r.path.name for r in results if r.success and r.path]

        body = (
            f"[success]{ok}[/success] images saved to "
            f"[accent]{dest_dir.resolve()}[/accent]\n\n"
        )
        for f in files[:10]:
            body += f"  [muted]•[/muted] {f}\n"
        if len(files) > 10:
            body += f"  [muted]…and {len(files) - 10} more[/muted]\n"

        panel = Panel(
            body,
            title="[title]▸ Done[/title]",
            border_style="border",
            padding=(1, 2),
        )
        self.console.print()
        self.console.print(panel)

    # ── Errors ───────────────────────────────────────────────────────

    def show_error(self, message: str) -> None:
        self.console.print(f"  [error]✘ {message}[/error]")

    # ── Main interaction loop ────────────────────────────────────────

    def run(self) -> None:
        """Start the interactive TUI loop."""
        self.show_banner()

        while True:
            self.show_divider()
            query = self.prompt_query()
            if not query:
                self.console.print("\n[muted]Goodbye! ■[/muted]\n")
                break

            max_results = self.prompt_max_results()

            # 1. Search
            try:
                results = self.run_search(query, max_results)
            except Exception as exc:
                self.show_error(f"Search failed: {exc}")
                continue

            if not results:
                self.show_error("No results found. Try a different query.")
                continue

            # Show results table
            self.show_results_table(results)

            # 2. Download
            folder = _sanitize_folder_name(query)
            dest_dir = Path("downloads") / folder
            urls = [r.url for r in results if r.url]

            try:
                dl_results = self.run_downloads(urls, dest_dir)
            except Exception as exc:
                self.show_error(f"Download failed: {exc}")
                continue

            # 3. ASCII previews
            self.show_ascii_previews(dl_results)

            # 4. Summary
            self.show_summary(dest_dir, dl_results)
