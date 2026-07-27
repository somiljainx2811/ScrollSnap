"""
ScrollSnap
==========

Preview Controller

The UI-facing entry point for the preview-before-save workflow:
opening a captured/stitched image, applying edits and
annotations, and rendering the final exportable result.
"""

from __future__ import annotations

from typing import Any

from core.event_bus import EventBus, event_bus as default_event_bus
from image_processing.editing_renderer import render_plan
from image_processing.pillow_backend import PillowMaskBackend
from preview.preview_window import PreviewWindow
from shapes.base_shape import Shape
from shapes.mask_renderer import MaskRenderer


class PreviewController:
    """
    Coordinates the preview/edit/annotate/export workflow for a
    stitched or single-frame image.
    """

    def __init__(self, bus: EventBus | None = None) -> None:

        self._bus = bus or default_event_bus

        self._window = PreviewWindow(bus=self._bus)

        self._mask_renderer = MaskRenderer(
            backend=PillowMaskBackend()
        )

    @property
    def window(self) -> PreviewWindow:
        return self._window

    def open(self, images: list[Any] | Any) -> None:
        self._window.open(images)

    def render_current(self) -> Any:
        """
        Render the currently open image with all edits and
        annotations burned in (without transitioning state).
        """

        plan = self._window.build_plan()

        return render_plan(plan.source, plan.edits, plan.annotations)

    def render_for_export(self) -> Any:
        """
        Transition to EXPORTING and render the final image.
        """

        plan = self._window.request_export()

        return render_plan(plan.source, plan.edits, plan.annotations)

    def apply_shape_cutout(self, shape: Shape) -> Any:
        """
        Apply a capture shape (circle, star, polygon, ...) to the
        current rendered preview, producing a transparent cutout.
        """

        image = self.render_current()

        mask_result = self._mask_renderer.render(
            shape, image.width, image.height
        )

        if not mask_result.success:
            raise RuntimeError(mask_result.error)

        return self._mask_renderer.backend.apply(
            image, mask_result.mask
        )
