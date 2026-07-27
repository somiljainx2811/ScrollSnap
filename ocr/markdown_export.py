"""
ScrollSnap
==========

Markdown Export

Writes extracted OCR text out as a plain Markdown file.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def export_markdown(
    text: str,
    path: str | Path,
    title: str = "Extracted Text",
) -> Path:
    """
    Write `text` to `path` as a simple Markdown document.
    """

    path = Path(path)

    if path.suffix.lower() != ".md":
        path = path.with_suffix(".md")

    path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    content = (
        f"# {title}\n\n"
        f"*Extracted by ScrollSnap OCR - {timestamp}*\n\n"
        "---\n\n"
        f"{text.strip()}\n"
    )

    path.write_text(content, encoding="utf-8")

    return path
