"""
ASCII art thumbnail renderer.

Converts an image file into a block of ASCII characters that
approximates the image when viewed in a monospace terminal.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

# Characters ordered from darkest to lightest.  The extended ramp gives
# smoother gradients than the classic short ramp.
CHARS = " .:-=+*#%@"


def image_to_ascii(
    path: Path,
    width: int = 60,
    height_ratio: float = 0.45,
) -> str:
    """
    Render an image file as an ASCII string.

    Args:
        path:         Path to an image file (JPEG, PNG, etc.).
        width:        Desired width in characters.
        height_ratio: Aspect-ratio correction factor.  Terminal characters
                      are roughly twice as tall as they are wide, so we
                      scale the height down by this factor.

    Returns:
        A multi-line string of ASCII art.
    """
    try:
        img = Image.open(path)
    except Exception:
        return "(preview unavailable)"

    # Compute output height preserving aspect ratio
    orig_w, orig_h = img.size
    if orig_w == 0:
        return "(preview unavailable)"
    aspect = orig_h / orig_w
    height = int(width * aspect * height_ratio)
    height = max(height, 1)

    # Resize and convert to greyscale
    img = img.resize((width, height), Image.Resampling.LANCZOS)
    img = img.convert("L")

    # Map each pixel to a character
    pixels = list(img.getdata())
    bucket_size = 256 / len(CHARS)
    lines: list[str] = []

    for row in range(height):
        start = row * width
        row_pixels = pixels[start : start + width]
        line = "".join(
            CHARS[min(int(px / bucket_size), len(CHARS) - 1)]
            for px in row_pixels
        )
        lines.append(line)

    return "\n".join(lines)
