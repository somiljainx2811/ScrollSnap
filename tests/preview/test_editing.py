"""
Tests for preview.editing.EditingSession.
"""

from __future__ import annotations

import pytest

from models.rectangle import Rectangle
from preview.editing import EditingSession, EditKind


class TestEditingSession:

    def test_crop_updates_current_size(self):

        session = EditingSession((800, 600))

        session.crop(Rectangle.from_xywh(0, 0, 400, 300))

        assert session.current_size() == (400, 300)

    def test_rotate_90_swaps_dimensions(self):

        session = EditingSession((800, 600))

        session.rotate(90)

        assert session.current_size() == (600, 800)

    def test_rotate_normalizes_to_0_360(self):

        session = EditingSession((100, 100))

        session.rotate(-90)

        assert session.operations[-1].value == 270

    def test_flip_does_not_change_size(self):

        session = EditingSession((800, 600))

        session.flip_horizontal()

        assert session.current_size() == (800, 600)

    def test_crop_outside_bounds_raises(self):

        session = EditingSession((100, 100))

        with pytest.raises(Exception):
            session.crop(Rectangle(200, 200, 300, 300))

    def test_undo_redo(self):

        session = EditingSession((800, 600))

        session.crop(Rectangle.from_xywh(0, 0, 400, 300))

        assert session.current_size() == (400, 300)

        assert session.undo()

        assert session.current_size() == (800, 600)

        assert session.redo()

        assert session.current_size() == (400, 300)

    def test_repeated_brightness_collapses_into_one_operation(self):

        session = EditingSession((100, 100))

        session.set_brightness(1.1)

        session.set_brightness(1.2)

        session.set_brightness(1.3)

        brightness_ops = [
            op for op in session.operations if op.kind == EditKind.BRIGHTNESS
        ]

        assert len(brightness_ops) == 1

        assert brightness_ops[0].value == 1.3

    def test_plan_serializes_crop_as_dict(self):

        session = EditingSession((800, 600))

        session.crop(Rectangle.from_xywh(0, 0, 400, 300))

        plan = session.plan()

        assert plan[0]["kind"] == "CROP"

        assert plan[0]["value"]["right"] == 400
