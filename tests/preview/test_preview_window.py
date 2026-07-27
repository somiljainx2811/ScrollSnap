"""
Tests for preview.preview_window.PreviewWindow and the
image_processing.editing_renderer rendering backend.
"""

from __future__ import annotations

import pytest
from PIL import Image

from core.exceptions import PreviewError
from image_processing.editing_renderer import render_plan
from models.rectangle import Rectangle
from preview.annotations import Annotation, AnnotationType
from preview.preview_window import PreviewState, PreviewWindow


def make_window(images=None):

    window = PreviewWindow()

    window.open(images or [Image.new("RGB", (400, 300), (10, 20, 30))])

    return window


class TestPreviewWindowStateMachine:

    def test_opens_into_viewing_state(self):

        window = make_window()

        assert window.state == PreviewState.VIEWING

    def test_invalid_transition_raises(self):

        window = make_window()

        window.enter_editing()

        with pytest.raises(PreviewError):
            window.enter_comparing()  # EDITING -> COMPARING not allowed

    def test_editing_to_annotating_allowed_directly(self):

        window = make_window()

        window.enter_editing()

        window.enter_annotating()

        assert window.state == PreviewState.ANNOTATING

    def test_close_from_any_open_state(self):

        window = make_window()

        window.enter_editing()

        window.close()

        assert window.state == PreviewState.CLOSED


class TestPreviewWindowNavigation:

    def test_multiple_images_navigable(self):

        images = [
            Image.new("RGB", (100, 100), (255, 0, 0)),
            Image.new("RGB", (200, 200), (0, 255, 0)),
        ]

        window = make_window(images)

        assert window.viewer.image_size == (100, 100)

        window.next_image()

        assert window.viewer.image_size == (200, 200)

    def test_navigating_resets_editing_session(self):

        images = [
            Image.new("RGB", (100, 100)),
            Image.new("RGB", (200, 200)),
        ]

        window = make_window(images)

        window.enter_editing()

        window.crop(Rectangle.from_xywh(0, 0, 50, 50))

        window.return_to_viewing()

        window.next_image()

        assert not window.editing.has_edits


class TestPreviewWindowExportPlan:

    def test_build_plan_includes_edits_and_annotations(self):

        window = make_window()

        window.enter_editing()

        window.crop(Rectangle.from_xywh(0, 0, 100, 100))

        window.return_to_viewing()

        window.enter_annotating()

        window.annotations.add(
            Annotation(AnnotationType.TEXT, points=[(5, 5)], text="hi")
        )

        window.return_to_viewing()

        plan = window.build_plan()

        assert plan.output_size == (100, 100)

        assert len(plan.edits) == 1

        assert len(plan.annotations) == 1

    def test_render_plan_produces_correct_size_image(self):

        window = make_window()

        window.enter_editing()

        window.crop(Rectangle.from_xywh(0, 0, 120, 90))

        window.return_to_viewing()

        plan = window.build_plan()

        rendered = render_plan(plan.source, plan.edits, plan.annotations)

        assert rendered.size == (120, 90)


class TestUndoRedo:

    def test_undo_reverts_last_edit(self):

        window = make_window()

        window.enter_editing()

        window.crop(Rectangle.from_xywh(0, 0, 100, 100))

        assert window.editing.current_size() == (100, 100)

        assert window.undo()

        assert window.editing.current_size() == (400, 300)
