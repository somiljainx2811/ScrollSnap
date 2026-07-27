"""
Tests for image_processing.pillow_backend.PillowMaskBackend and
shapes.mask_renderer.MaskRenderer working together.
"""

from __future__ import annotations

import pytest
from PIL import Image

from image_processing.pillow_backend import PillowMaskBackend
from shapes.bezier import BezierCurve, BezierShape
from shapes.circle import CircleShape
from shapes.ellipse import EllipseShape
from shapes.freehand import FreehandShape
from shapes.mask_renderer import MaskRenderer
from shapes.polygon import Point, PolygonShape
from shapes.rectangle import RectangleShape
from shapes.rounded_rectangle import RoundedRectangleShape
from shapes.star import StarShape


ALL_SHAPES = [
    RectangleShape(20, 20, 100, 80),
    CircleShape(50, 50, 40),
    EllipseShape(30, 30, 120, 60),
    RoundedRectangleShape(10, 10, 150, 100, 15),
    PolygonShape([Point(10, 10), Point(100, 10), Point(60, 90)]),
    StarShape(center_x=100, center_y=100, outer_radius=60, inner_radius=25),
    FreehandShape(
        [Point(5, 5), Point(80, 5), Point(80, 80), Point(5, 80)]
    ),
    BezierShape(
        [BezierCurve(Point(0, 50), Point(30, 0), Point(70, 0), Point(100, 50))]
    ),
]


@pytest.fixture
def renderer():
    return MaskRenderer(backend=PillowMaskBackend())


@pytest.fixture
def base_image():
    return Image.new("RGB", (200, 200), (10, 20, 30))


@pytest.mark.parametrize("shape", ALL_SHAPES, ids=lambda s: type(s).__name__)
def test_mask_render_succeeds_for_every_shape(renderer, base_image, shape):

    result = renderer.render(shape, base_image.width, base_image.height)

    assert result.success, result.error

    assert result.mask is not None


@pytest.mark.parametrize("shape", ALL_SHAPES, ids=lambda s: type(s).__name__)
def test_apply_produces_rgba_cutout(renderer, base_image, shape):

    result = renderer.render(shape, base_image.width, base_image.height)

    cutout = renderer.backend.apply(base_image, result.mask)

    assert cutout.mode == "RGBA"

    assert cutout.width > 0 and cutout.height > 0


def test_cutout_is_transparent_outside_shape(renderer, base_image):

    shape = CircleShape(50, 50, 30)  # bounding box (50,50)-(110,110)

    result = renderer.render(shape, base_image.width, base_image.height)

    cutout = renderer.backend.apply(base_image, result.mask)

    # A corner of the full canvas, far from the circle, should be
    # fully cropped away (bbox crop) or transparent if still present.
    full_rgba = base_image.convert("RGBA")

    full_rgba.putalpha(result.mask)

    corner_alpha = full_rgba.getpixel((0, 0))[3]

    assert corner_alpha == 0
