#!/usr/bin/env python3
"""
PixelSearch — Terminal Image Search TUI
========================================

A retro-themed terminal tool that searches for images on the web,
downloads them locally, and renders ASCII art previews.

Usage:
    python main.py

Dependencies (install first):
    pip install -r requirements.txt

Modules:
    pixelsearch/
        scraper.py     – DuckDuckGo image search (no API key needed)
        downloader.py  – Async parallel downloads with retry logic
        ascii_art.py   – PIL-based image → ASCII art renderer
        tui.py         – Rich-powered retro terminal interface
"""

from pixelsearch.tui import PixelSearchTUI


def main() -> None:
    app = PixelSearchTUI()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")


if __name__ == "__main__":
    main()
