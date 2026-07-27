"""
ScrollSnap
==========

OCR Summary Plugin

Logs a short summary (word count, confidence) every time OCR
text is extracted, and warns when confidence is low enough that
the result might be unreliable.
"""

from __future__ import annotations

from plugins.api import Plugin, PluginContext
from utils.logger import get_logger


logger = get_logger("plugin.ocr_summary")

LOW_CONFIDENCE_THRESHOLD = 60.0


class OCRSummaryPlugin(Plugin):

    name = "OCR Summary"

    version = "1.0.0"

    description = (
        "Logs a summary after every OCR extraction and flags "
        "low-confidence results."
    )

    def activate(self, context: PluginContext) -> None:

        self._context = context

        self._subscribe(context, "ocr.extracted", self._on_extracted)

    def _on_extracted(self, event) -> None:

        result = event.data

        if result is None:
            return

        logger.info(
            "OCR extracted %d word(s) at %.1f%% confidence.",
            result.word_count, result.confidence,
        )

        if 0 < result.confidence < LOW_CONFIDENCE_THRESHOLD:

            self._context.notify(
                "Low-Confidence OCR Result",
                "The extracted text may contain errors "
                f"(confidence: {result.confidence:.0f}%).",
            )
