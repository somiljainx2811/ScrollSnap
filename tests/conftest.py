"""
ScrollSnap
==========

Pytest configuration and shared fixtures.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------
# Environment-dependent skip markers
# ---------------------------------------------------------

HAS_DISPLAY = bool(os.environ.get("DISPLAY"))

requires_display = pytest.mark.skipif(
    not HAS_DISPLAY,
    reason="No DISPLAY available (needs a real or virtual X server).",
)


def _has_tesseract() -> bool:

    return shutil.which("tesseract") is not None


requires_tesseract = pytest.mark.skipif(
    not _has_tesseract(),
    reason="tesseract-ocr binary is not installed.",
)


# ---------------------------------------------------------
# Fixtures
# ---------------------------------------------------------

@pytest.fixture
def solid_image():
    """A small solid-color RGB image."""

    def _make(width=200, height=150, color=(40, 60, 90)):
        return Image.new("RGB", (width, height), color)

    return _make


@pytest.fixture
def text_image():
    """An RGB image containing rendered text, for OCR tests."""

    def _make(text="ScrollSnap Test", width=600, height=180):

        image = Image.new("RGB", (width, height), (255, 255, 255))

        draw = ImageDraw.Draw(image)

        font = _load_ocr_test_font(32)

        draw.text((20, 40), text, fill=(0, 0, 0), font=font)

        return image

    return _make


def _load_ocr_test_font(size: int):
    """
    PIL's default bitmap font is small and pixelated enough that
    Tesseract sometimes misreads it (e.g. "S" -> "Se"); a real
    TrueType font at a reasonable size gives OCR tests a fair,
    non-flaky shot at recognizing the text.
    """

    from PIL import ImageFont

    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "DejaVuSans-Bold.ttf",
        "Arial.ttf",
    )

    for candidate in candidates:

        try:
            return ImageFont.truetype(candidate, size)

        except OSError:
            continue

    return ImageFont.load_default()


@pytest.fixture
def tmp_project_dir(tmp_path):
    """
    An isolated temp directory tests can use as a stand-in
    project root for storage/cache-writing modules.
    """

    return tmp_path
