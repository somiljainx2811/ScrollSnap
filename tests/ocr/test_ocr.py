"""
Tests for the OCR pipeline: text extraction, Markdown export,
and searchable PDF export. Skipped entirely if the `tesseract`
binary isn't installed.
"""

from __future__ import annotations

import pytest

from tests.conftest import requires_tesseract


@requires_tesseract
class TestTextExtractor:

    def test_extracts_known_text(self, text_image):

        from ocr.text_extractor import TextExtractor

        image = text_image("ScrollSnap")

        result = TextExtractor().extract(image)

        assert "ScrollSnap" in result.text

        assert result.word_count >= 1

        assert 0 <= result.confidence <= 100

    def test_empty_image_yields_empty_result(self, solid_image):

        from ocr.text_extractor import TextExtractor

        result = TextExtractor().extract(solid_image(color=(255, 255, 255)))

        assert result.is_empty


@requires_tesseract
class TestMarkdownExport:

    def test_writes_markdown_file(self, tmp_path):

        from ocr.markdown_export import export_markdown

        path = export_markdown(
            "hello world", tmp_path / "out", title="My Title"
        )

        assert path.suffix == ".md"

        content = path.read_text()

        assert "My Title" in content

        assert "hello world" in content


@requires_tesseract
class TestSearchablePdfExport:

    def test_writes_valid_pdf(self, text_image, tmp_path):

        from ocr.searchable_pdf import export_searchable_pdf

        image = text_image("Searchable PDF Test")

        path = export_searchable_pdf(image, tmp_path / "out")

        assert path.exists()

        assert path.suffix == ".pdf"

        assert path.read_bytes()[:4] == b"%PDF"


@requires_tesseract
class TestOCRController:

    def test_full_pipeline(self, text_image, tmp_path):

        from controllers.ocr_controller import OCRController

        controller = OCRController()

        image = text_image("Controller Test")

        result = controller.extract_text(image)

        assert "Controller" in result.text or "Test" in result.text

        md_path = controller.export_markdown(result.text, tmp_path / "a.md")

        assert md_path.exists()

        pdf_path = controller.export_searchable_pdf(image, tmp_path / "a.pdf")

        assert pdf_path.exists()
