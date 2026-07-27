"""
ScrollSnap
==========

Comparison View

Supports comparing two images inside the preview: the original
capture versus an edited result, or any two frames a user wants
to inspect side by side.

Responsibilities
----------------
- Hold "before" and "after" images
- Track comparison mode (slider, side-by-side, overlay)
- Compute the clip / split rectangles a renderer needs to draw
  each half of the comparison
- Track slider position and overlay opacity

Does NOT:
- Render pixels
- Load or decode images
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from core.exceptions import PreviewError
from models.rectangle import Rectangle


class ComparisonMode(Enum):
    """
    Supported comparison layouts.
    """

    SLIDER = auto()

    SIDE_BY_SIDE = auto()

    OVERLAY = auto()

    TOGGLE = auto()


class SliderOrientation(Enum):
    """
    Direction the comparison slider drags along.
    """

    HORIZONTAL = auto()

    VERTICAL = auto()


@dataclass(slots=True)
class ComparisonLayout:
    """
    Computed geometry describing how to draw the comparison for
    the current mode.
    """

    before_clip: Rectangle

    after_clip: Rectangle

    divider_position: float


class ComparisonView:
    """
    Manages a before/after comparison of two images.
    """

    def __init__(
        self,
        before: Any = None,
        after: Any = None,
        mode: ComparisonMode = ComparisonMode.SLIDER,
        orientation: SliderOrientation = (
            SliderOrientation.HORIZONTAL
        ),
    ) -> None:

        self._before = before

        self._after = after

        self._mode = mode

        self._orientation = orientation

        self._slider_position = 0.5

        self._overlay_opacity = 0.5

        self._showing_after = True

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def before(self) -> Any:
        return self._before

    @property
    def after(self) -> Any:
        return self._after

    @property
    def mode(self) -> ComparisonMode:
        return self._mode

    @property
    def orientation(self) -> SliderOrientation:
        return self._orientation

    @property
    def slider_position(self) -> float:
        return self._slider_position

    @property
    def overlay_opacity(self) -> float:
        return self._overlay_opacity

    @property
    def has_both_images(self) -> bool:
        return self._before is not None and self._after is not None

    @property
    def is_showing_after(self) -> bool:
        return self._showing_after

    # ---------------------------------------------------------
    # Configuration
    # ---------------------------------------------------------

    def set_images(self, before: Any, after: Any) -> None:
        self._before = before
        self._after = after

    def set_mode(self, mode: ComparisonMode) -> None:
        self._mode = mode

    def set_orientation(
        self,
        orientation: SliderOrientation,
    ) -> None:
        self._orientation = orientation

    def swap(self) -> None:
        """
        Swap before and after.
        """

        self._before, self._after = self._after, self._before

    def set_slider_position(self, position: float) -> float:
        """
        Set the divider position as a fraction (0.0 - 1.0) of
        the viewport along the active orientation.
        """

        self._slider_position = max(0.0, min(1.0, position))

        return self._slider_position

    def set_overlay_opacity(self, opacity: float) -> float:

        self._overlay_opacity = max(0.0, min(1.0, opacity))

        return self._overlay_opacity

    def toggle(self) -> bool:
        """
        Flip which image is shown, for TOGGLE mode.
        """

        self._showing_after = not self._showing_after

        return self._showing_after

    # ---------------------------------------------------------
    # Layout
    # ---------------------------------------------------------

    def layout(
        self,
        viewport_size: tuple[float, float],
    ) -> ComparisonLayout:
        """
        Compute clip rectangles for the "before" and "after"
        images given the current mode and viewport size.
        """

        if not self.has_both_images:
            raise PreviewError(
                "Comparison requires both a 'before' and "
                "'after' image."
            )

        viewport_width, viewport_height = viewport_size

        full = Rectangle.from_xywh(
            0, 0, viewport_width, viewport_height,
        )

        if self._mode == ComparisonMode.SIDE_BY_SIDE:
            return self._side_by_side_layout(
                viewport_width, viewport_height,
            )

        if self._mode == ComparisonMode.SLIDER:
            return self._slider_layout(
                viewport_width, viewport_height,
            )

        if self._mode == ComparisonMode.OVERLAY:

            return ComparisonLayout(
                before_clip=full,
                after_clip=full,
                divider_position=self._overlay_opacity,
            )

        # TOGGLE: only one image is visible at a time.
        visible = full if self._showing_after else Rectangle.empty()

        hidden = Rectangle.empty() if self._showing_after else full

        return ComparisonLayout(
            before_clip=hidden,
            after_clip=visible,
            divider_position=1.0 if self._showing_after else 0.0,
        )

    def _side_by_side_layout(
        self,
        viewport_width: float,
        viewport_height: float,
    ) -> ComparisonLayout:

        if self._orientation == SliderOrientation.HORIZONTAL:

            half = viewport_width / 2

            before_clip = Rectangle.from_xywh(
                0, 0, half, viewport_height,
            )

            after_clip = Rectangle.from_xywh(
                half, 0, viewport_width - half, viewport_height,
            )

        else:

            half = viewport_height / 2

            before_clip = Rectangle.from_xywh(
                0, 0, viewport_width, half,
            )

            after_clip = Rectangle.from_xywh(
                0, half, viewport_width, viewport_height - half,
            )

        return ComparisonLayout(
            before_clip=before_clip,
            after_clip=after_clip,
            divider_position=0.5,
        )

    def _slider_layout(
        self,
        viewport_width: float,
        viewport_height: float,
    ) -> ComparisonLayout:

        if self._orientation == SliderOrientation.HORIZONTAL:

            split = viewport_width * self._slider_position

            before_clip = Rectangle.from_xywh(
                0, 0, split, viewport_height,
            )

            after_clip = Rectangle.from_xywh(
                split, 0, viewport_width - split, viewport_height,
            )

        else:

            split = viewport_height * self._slider_position

            before_clip = Rectangle.from_xywh(
                0, 0, viewport_width, split,
            )

            after_clip = Rectangle.from_xywh(
                0, split, viewport_width, viewport_height - split,
            )

        return ComparisonLayout(
            before_clip=before_clip,
            after_clip=after_clip,
            divider_position=self._slider_position,
        )

    def __repr__(self) -> str:

        return (
            "ComparisonView("
            f"mode={self._mode.name}, "
            f"slider={self._slider_position:.2f}"
            ")"
        )
