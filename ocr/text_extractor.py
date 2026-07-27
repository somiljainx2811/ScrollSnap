"""
ScrollSnap
==========

Text Extractor

Extracts text from a captured/stitched image using Tesseract
OCR (via `pytesseract`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytesseract


@dataclass(slots=True)
class TextExtractionResult:
    """
    Result of running OCR over an image.
    """

    text: str

    confidence: float

    word_count: int

    language: str

    @property
    def is_empty(self) -> bool:
        return not self.text.strip()


class TextExtractor:
    """
    Thin wrapper around Tesseract for plain-text extraction.
    """

    def __init__(self, language: str = "eng") -> None:
        self.language = language

    def extract(
        self,
        image: Any,
        language: str | None = None,
    ) -> TextExtractionResult:
        """
        Run OCR over `image`, returning the recognized text plus
        a rough word-level confidence average.
        """

        lang = language or self.language

        text = pytesseract.image_to_string(image, lang=lang)

        data = pytesseract.image_to_data(
            image, lang=lang, output_type=pytesseract.Output.DICT
        )

        confidences = [
            float(c) for c in data.get("conf", []) if _is_number(c)
            and float(c) >= 0
        ]

        average_confidence = (
            sum(confidences) / len(confidences) if confidences else 0.0
        )

        words = [w for w in text.split() if w.strip()]

        return TextExtractionResult(
            text=text.strip(),
            confidence=average_confidence,
            word_count=len(words),
            language=lang,
        )

    def available_languages(self) -> list[str]:

        try:
            return pytesseract.get_languages(config="")

        except Exception:
            return [self.language]


def _is_number(value: Any) -> bool:

    try:
        float(value)
        return True

    except (TypeError, ValueError):
        return False
