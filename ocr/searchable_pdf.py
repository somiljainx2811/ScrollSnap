"""
ScrollSnap
==========

Searchable PDF Export

Wraps a captured/stitched image in a PDF with an invisible OCR
text layer, so the resulting file is searchable/selectable while
still displaying the original image.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytesseract


def export_searchable_pdf(
    image: Any,
    path: str | Path,
    language: str = "eng",
) -> Path:
    """
    Write `image` to `path` as a searchable PDF.
    """

    path = Path(path)

    if path.suffix.lower() != ".pdf":
        path = path.with_suffix(".pdf")

    path.parent.mkdir(parents=True, exist_ok=True)

    pdf_bytes = pytesseract.image_to_pdf_or_hocr(
        image, lang=language, extension="pdf"
    )

    with path.open("wb") as handle:
        handle.write(pdf_bytes)

    return path
