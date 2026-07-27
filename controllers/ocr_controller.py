"""
ScrollSnap
==========

OCR Controller

The UI-facing entry point for text extraction, searchable PDF
export, and Markdown export.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.event_bus import EventBus, event_bus as default_event_bus
from ocr.markdown_export import export_markdown
from ocr.searchable_pdf import export_searchable_pdf
from ocr.text_extractor import TextExtractionResult, TextExtractor


class OCRController:
    """
    Coordinates OCR text extraction and export.
    """

    def __init__(
        self,
        language: str = "eng",
        bus: EventBus | None = None,
    ) -> None:

        self._bus = bus or default_event_bus

        self._extractor = TextExtractor(language=language)

        self._last_result: TextExtractionResult | None = None

    @property
    def last_result(self) -> TextExtractionResult | None:
        return self._last_result

    def extract_text(
        self,
        image: Any,
        language: str | None = None,
    ) -> TextExtractionResult:

        result = self._extractor.extract(image, language=language)

        self._last_result = result

        self._bus.publish("ocr.extracted", result)

        return result

    def available_languages(self) -> list[str]:
        return self._extractor.available_languages()

    def export_markdown(
        self,
        text: str,
        path: str | Path,
        title: str = "Extracted Text",
    ) -> Path:

        written = export_markdown(text, path, title=title)

        self._bus.publish("ocr.markdown_exported", written)

        return written

    def export_searchable_pdf(
        self,
        image: Any,
        path: str | Path,
        language: str | None = None,
    ) -> Path:

        written = export_searchable_pdf(
            image, path, language=language or self._extractor.language
        )

        self._bus.publish("ocr.pdf_exported", written)

        return written
