"""
ScrollSnap
==========

Zoom Controller

Manages zoom level state for the preview image viewer.

Responsibilities
----------------
- Track current zoom level
- Enforce minimum / maximum zoom bounds
- Provide step-based zoom in / zoom out
- Compute "fit width", "fit height" and "fit page" levels
- Notify listeners when the zoom level changes

Does NOT:
- Render images
- Know about pixels, canvases, or widgets
- Handle panning
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from constants import (
    DEFAULT_ZOOM,
    MAX_ZOOM,
    MIN_ZOOM,
)


ZOOM_STEP = 1.25

FIT_PADDING = 0.0


@dataclass(slots=True)
class ZoomState:
    """
    Immutable snapshot of the zoom controller.
    """

    level: float

    min_zoom: float

    max_zoom: float

    @property
    def percentage(self) -> int:
        return round(self.level * 100)

    @property
    def at_minimum(self) -> bool:
        return self.level <= self.min_zoom

    @property
    def at_maximum(self) -> bool:
        return self.level >= self.max_zoom


class ZoomController:
    """
    Controls the zoom level of a preview viewer.
    """

    def __init__(
        self,
        min_zoom: float = MIN_ZOOM,
        max_zoom: float = MAX_ZOOM,
        initial: float = DEFAULT_ZOOM,
    ) -> None:

        if min_zoom <= 0:
            raise ValueError(
                "min_zoom must be positive."
            )

        if max_zoom < min_zoom:
            raise ValueError(
                "max_zoom must be >= min_zoom."
            )

        self._min_zoom = min_zoom

        self._max_zoom = max_zoom

        self._level = self._clamp(initial)

        self._listeners: list[Callable[[float], None]] = []

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def level(self) -> float:
        return self._level

    @property
    def min_zoom(self) -> float:
        return self._min_zoom

    @property
    def max_zoom(self) -> float:
        return self._max_zoom

    @property
    def can_zoom_in(self) -> bool:
        return self._level < self._max_zoom

    @property
    def can_zoom_out(self) -> bool:
        return self._level > self._min_zoom

    @property
    def is_default(self) -> bool:
        return abs(self._level - DEFAULT_ZOOM) < 1e-6

    def snapshot(self) -> ZoomState:
        return ZoomState(
            level=self._level,
            min_zoom=self._min_zoom,
            max_zoom=self._max_zoom,
        )

    # ---------------------------------------------------------
    # Mutators
    # ---------------------------------------------------------

    def set(self, level: float) -> float:
        """
        Set an explicit zoom level.

        Returns the clamped resulting level.
        """

        return self._apply(level)

    def zoom_in(self, factor: float = ZOOM_STEP) -> float:
        """
        Increase zoom by a multiplicative factor.
        """

        return self._apply(self._level * factor)

    def zoom_out(self, factor: float = ZOOM_STEP) -> float:
        """
        Decrease zoom by a multiplicative factor.
        """

        return self._apply(self._level / factor)

    def reset(self) -> float:
        """
        Reset to the default (100%) zoom level.
        """

        return self._apply(DEFAULT_ZOOM)

    def fit_width(
        self,
        image_width: float,
        viewport_width: float,
    ) -> float:
        """
        Compute and apply a level that fits image width
        exactly inside the viewport width.
        """

        return self._apply(
            self._fit_ratio(image_width, viewport_width)
        )

    def fit_height(
        self,
        image_height: float,
        viewport_height: float,
    ) -> float:
        """
        Compute and apply a level that fits image height
        exactly inside the viewport height.
        """

        return self._apply(
            self._fit_ratio(image_height, viewport_height)
        )

    def fit_page(
        self,
        image_size: tuple[float, float],
        viewport_size: tuple[float, float],
    ) -> float:
        """
        Compute and apply a level that fits the entire image
        inside the viewport, preserving aspect ratio.
        """

        image_width, image_height = image_size

        viewport_width, viewport_height = viewport_size

        width_ratio = self._fit_ratio(
            image_width,
            viewport_width,
        )

        height_ratio = self._fit_ratio(
            image_height,
            viewport_height,
        )

        return self._apply(
            min(width_ratio, height_ratio)
        )

    # ---------------------------------------------------------
    # Listeners
    # ---------------------------------------------------------

    def subscribe(
        self,
        callback: Callable[[float], None],
    ) -> None:

        if callback not in self._listeners:
            self._listeners.append(callback)

    def unsubscribe(
        self,
        callback: Callable[[float], None],
    ) -> None:

        if callback in self._listeners:
            self._listeners.remove(callback)

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _fit_ratio(
        self,
        content_size: float,
        viewport_size: float,
    ) -> float:

        if content_size <= 0:
            return DEFAULT_ZOOM

        usable = viewport_size * (1.0 - FIT_PADDING)

        return usable / content_size

    def _clamp(self, level: float) -> float:

        return max(
            self._min_zoom,
            min(self._max_zoom, level),
        )

    def _apply(self, level: float) -> float:

        clamped = self._clamp(level)

        if clamped != self._level:

            self._level = clamped

            self._notify()

        return self._level

    def _notify(self) -> None:

        for listener in list(self._listeners):
            listener(self._level)

    def __repr__(self) -> str:

        return (
            "ZoomController("
            f"level={self._level:.3f}, "
            f"percentage={round(self._level * 100)}%"
            ")"
        )
