# PixelSearch

A retro-themed terminal image search tool. Search for images from the command line, download them locally, and preview them as ASCII art — all without leaving your terminal.

```
 ██████╗ ██╗██╗  ██╗███████╗██╗     ███████╗███████╗ █████╗ ██████╗  ██████╗██╗  ██╗
 ██╔══██╗██║╚██╗██╔╝██╔════╝██║     ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██║  ██║
 ██████╔╝██║ ╚███╔╝ █████╗  ██║     ███████╗█████╗  ███████║██████╔╝██║     ███████║
 ██╔═══╝ ██║ ██╔██╗ ██╔══╝  ██║     ╚════██║██╔══╝  ██╔══██║██╔══██╗██║     ██╔══██║
 ██║     ██║██╔╝ ██╗███████╗███████╗███████║███████╗██║  ██║██║  ██║╚██████╗██║  ██║
 ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
```

## Features

- **Free image search** — Powered by DuckDuckGo, no API keys or payments required
- **Async parallel downloads** — Up to 8 concurrent downloads via `aiohttp` for maximum speed
- **ASCII art previews** — Downloaded images rendered as ASCII thumbnails directly in the terminal
- **Retro pixel UI** — Styled terminal interface with green/cyan/magenta theme using Rich
- **Retry with backoff** — 3 attempts per image with exponential backoff (1s, 2s, 4s); 4xx errors skipped immediately
- **Safe search** — Moderate safe-search enabled by default
- **Organized output** — Images saved to `downloads/<query>/` with numbered, sanitized filenames
- **Interactive loop** — Search multiple queries in one session; type `q` to quit

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

You'll see the retro banner, then an interactive prompt:

```
>>> Enter search query (or 'q' to quit): mountain landscape
>>> How many images? (default 10, max 1000): 15
```

The app will search, display a results table, download the images with a live progress bar, show ASCII previews of the first 5, and print a summary of saved files.

## Dependencies

| Package | Purpose |
|---------|---------|
| [aiohttp](https://docs.aiohttp.org/) | Async HTTP client for parallel image downloads |
| [duckduckgo-search](https://github.com/deedy5/duckduckgo_search) | Free image search via DuckDuckGo scraping |
| [Pillow](https://python-pillow.org/) | Image processing for ASCII thumbnail generation |
| [rich](https://rich.readthedocs.io/) | Styled terminal UI — tables, progress bars, panels |

All are free, open-source, and installable via pip. **No paid APIs.**

## Project Structure

```
.
├── main.py                  # Entry point
├── requirements.txt         # pip dependencies
└── pixelsearch/
    ├── __init__.py          # Package version
    ├── scraper.py           # DuckDuckGo image search
    ├── downloader.py        # Async downloader with retry logic
    ├── ascii_art.py         # Image → ASCII art renderer
    └── tui.py               # Rich-powered retro terminal UI
```

### Module Overview

**`scraper.py`** — Wraps `duckduckgo-search` to return structured `ImageResult` objects with title, direct image URL, source page, and dimensions.

**`downloader.py`** — Downloads a list of image URLs concurrently with `aiohttp`. Uses a semaphore to cap parallelism at 8. Each download gets 3 retry attempts with exponential backoff. Client errors (4xx) are not retried. A progress callback fires after each image completes.

**`ascii_art.py`** — Opens an image with Pillow, resizes it to fit the terminal width, converts to greyscale, and maps each pixel to a character from the ramp ` .:-=+*#%@` (dark to light). Aspect ratio is corrected for monospace character proportions.

**`tui.py`** — Orchestrates the full interactive loop: banner display, query prompt, search with spinner, results table, download with progress bar, ASCII preview panels (up to 5), and a final summary. All output uses a custom Rich theme for the retro look.

## Example Output

```
>>> Enter search query (or 'q' to quit): sunset

  ✔ Found 10 image results.

┌──────────────────── ▸ Search Results ────────────────────┐
│  #  │ Title                    │    Size    │ URL        │
├─────┼──────────────────────────┼────────────┼────────────┤
│   1 │ Beautiful Sunset Over... │ 1920×1080  │ https://…  │
│   2 │ Ocean Sunset Wallpaper   │ 2560×1440  │ https://…  │
│ ... │                          │            │            │
└─────┴──────────────────────────┴────────────┴────────────┘

  Downloading to: downloads/sunset
  ⠋ Downloading images… ████████████████████████████ 10/10
  ✔ 10 downloaded

▸ ASCII Previews
╭─── 001_sunset.jpg ───╮
│ ..::--==++**##%%@@@@  │
│ ...::--==+**##%%@@    │
│ ....::--=++*##%%@     │
╰──────────────────────╯

╭──────────── ▸ Done ────────────╮
│  10 images saved to             │
│  /home/user/scraper/downloads/  │
│  sunset/                        │
│                                 │
│  • 001_sunset.jpg               │
│  • 002_ocean_sunset.jpg         │
│  • ...                          │
╰─────────────────────────────────╯
```

## Configuration

Constants can be adjusted in the source:

| Constant | File | Default | Description |
|----------|------|---------|-------------|
| `MAX_CONCURRENT` | `downloader.py` | `8` | Max parallel downloads |
| `RETRY_ATTEMPTS` | `downloader.py` | `3` | Retries per failed image |
| `RETRY_BASE_DELAY` | `downloader.py` | `1.0s` | Initial backoff delay |
| `DOWNLOAD_TIMEOUT` | `downloader.py` | `15s` | Per-image timeout |
| `CHARS` | `ascii_art.py` | ` .:-=+*#%@` | ASCII brightness ramp |

## Requirements

- Python 3.10+
- Internet connection
- A terminal that supports ANSI colors (most modern terminals)

## License

MIT
