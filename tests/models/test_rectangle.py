"""
Tests for models.rectangle.Rectangle, including a regression
test for the missing to_dict/from_dict methods (Frame and
CaptureRegion both depended on these but they didn't exist).
"""

from __future__ import annotations

from models.rectangle import Rectangle


class TestRectangleGeometry:

    def test_from_xywh(self):

        rect = Rectangle.from_xywh(10, 20, 100, 50)

        assert rect.width == 100

        assert rect.height == 50

        assert rect.right == 110

        assert rect.bottom == 70

    def test_contains_point(self):

        rect = Rectangle(0, 0, 100, 100)

        assert rect.contains_point((50, 50))

        assert not rect.contains_point((150, 50))

    def test_clip_returns_intersection(self):

        rect = Rectangle(0, 0, 100, 100)

        bounds = Rectangle(50, 50, 200, 200)

        clipped = rect.clip(bounds)

        assert clipped == Rectangle(50, 50, 100, 100)


class TestRectangleSerialization:
    """
    Regression test: `Rectangle.to_dict()`/`from_dict()` were
    referenced by `models.frame.Frame` and
    `models.capture_region.CaptureRegion` but never existed,
    which would have crashed any session save/load.
    """

    def test_to_dict_round_trip(self):

        original = Rectangle(1, 2, 300, 400)

        restored = Rectangle.from_dict(original.to_dict())

        assert restored == original

    def test_frame_serialization_round_trip(self):

        from models.frame import Frame

        frame = Frame(region=Rectangle.from_xywh(0, 0, 100, 100))

        restored = Frame.from_dict(frame.to_dict())

        assert restored.region == frame.region

    def test_capture_region_serialization_round_trip(self):

        from models.capture_region import CaptureRegion

        region = CaptureRegion(rectangle=Rectangle.from_xywh(0, 0, 50, 50))

        restored = CaptureRegion.from_dict(region.to_dict())

        assert restored.rectangle == region.rectangle
