"""
ScrollSnap
==========

Pan Controller

Manages viewport pan (scroll) offset for the preview image viewer.

Responsibilities
----------------
- Track current pan offset
- Handle drag gestures (start / update / end)
- Clamp offset so the image cannot be dragged out of view
- Support programmatic panning and centering

Does NOT:
- Render images
- Know about zoom math directly (it is given pre-computed bounds)
- Handle keyboard navigation
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PanOffset:
    """
    Immutable snapshot of the current pan offset.
    """

    x: float

    y: float

    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


class PanController:
    """
    Controls the pan offset of a preview viewer.
    """

    def __init__(self) -> None:

        self._x = 0.0

        self._y = 0.0

        self._dragging = False

        self._drag_start: tuple[float, float] | None = None

        self._drag_origin: tuple[float, float] | None = None

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    @property
    def offset(self) -> PanOffset:
        return PanOffset(self._x, self._y)

    @property
    def is_dragging(self) -> bool:
        return self._dragging

    @property
    def is_centered(self) -> bool:
        return self._x == 0.0 and self._y == 0.0

    # ---------------------------------------------------------
    # Programmatic Panning
    # ---------------------------------------------------------

    def pan_by(self, dx: float, dy: float) -> PanOffset:
        """
        Move the viewport by a relative amount.
        """

        self._x += dx

        self._y += dy

        return self.offset

    def pan_to(self, x: float, y: float) -> PanOffset:
        """
        Move the viewport to an absolute offset.
        """

        self._x = x

        self._y = y

        return self.offset

    def reset(self) -> PanOffset:
        """
        Reset pan back to the origin.
        """

        self._x = 0.0

        self._y = 0.0

        return self.offset

    def center_on(
        self,
        point: tuple[float, float],
        viewport_size: tuple[float, float],
        content_size: tuple[float, float],
    ) -> PanOffset:
        """
        Pan so that `point` (in content coordinates) is centered
        inside the viewport.
        """

        viewport_width, viewport_height = viewport_size

        content_width, content_height = content_size

        target_x = (viewport_width / 2) - point[0]

        target_y = (viewport_height / 2) - point[1]

        return self.pan_to(target_x, target_y)

    # ---------------------------------------------------------
    # Drag Gestures
    # ---------------------------------------------------------

    def start_drag(self, x: float, y: float) -> None:
        """
        Begin a drag gesture at a screen coordinate.
        """

        self._dragging = True

        self._drag_start = (x, y)

        self._drag_origin = (self._x, self._y)

    def update_drag(self, x: float, y: float) -> PanOffset:
        """
        Update the current drag gesture, returning the new offset.
        """

        if not self._dragging or self._drag_start is None:
            raise RuntimeError(
                "update_drag() called without an active drag."
            )

        start_x, start_y = self._drag_start

        origin_x, origin_y = self._drag_origin  # type: ignore[misc]

        self._x = origin_x + (x - start_x)

        self._y = origin_y + (y - start_y)

        return self.offset

    def end_drag(self) -> PanOffset:
        """
        End the current drag gesture.
        """

        self._dragging = False

        self._drag_start = None

        self._drag_origin = None

        return self.offset

    # ---------------------------------------------------------
    # Bounds Clamping
    # ---------------------------------------------------------

    def clamp_to_bounds(
        self,
        viewport_size: tuple[float, float],
        content_size: tuple[float, float],
        overscroll: float = 0.0,
    ) -> PanOffset:
        """
        Clamp the pan offset so the content stays reachable
        within the viewport, allowing an optional overscroll
        margin (in pixels) past each edge.
        """

        viewport_width, viewport_height = viewport_size

        content_width, content_height = content_size

        self._x = self._clamp_axis(
            self._x,
            viewport_width,
            content_width,
            overscroll,
        )

        self._y = self._clamp_axis(
            self._y,
            viewport_height,
            content_height,
            overscroll,
        )

        return self.offset

    @staticmethod
    def _clamp_axis(
        offset: float,
        viewport_length: float,
        content_length: float,
        overscroll: float,
    ) -> float:

        if content_length <= viewport_length:

            # Content fits entirely: keep it centered, no panning.
            return (viewport_length - content_length) / 2

        min_offset = viewport_length - content_length - overscroll

        max_offset = overscroll

        return max(min_offset, min(max_offset, offset))

    def __repr__(self) -> str:

        return (
            "PanController("
            f"x={self._x:.1f}, y={self._y:.1f}, "
            f"dragging={self._dragging}"
            ")"
        )
