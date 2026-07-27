"""
ScrollSnap
==========

Region Manager

Manages the currently selected capture region.

Responsibilities:
- Store the active capture region
- Validate regions
- Update or clear the selection
- Notify listeners when the region changes

This class contains no UI code and performs no screen capture.
"""

from __future__ import annotations

from collections.abc import Callable

from models.capture_region import CaptureRegion
from models.rectangle import Rectangle


RegionListener = Callable[[CaptureRegion | None], None]


class RegionManager:
    """
    Manages the application's active capture region.
    """

    def __init__(self) -> None:
        self._region: CaptureRegion | None = None
        self._listeners: list[RegionListener] = []

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def region(self) -> CaptureRegion | None:
        """
        Return the current capture region.
        """
        return self._region

    @property
    def has_region(self) -> bool:
        """
        True if a region has been selected.
        """
        return self._region is not None

    # ---------------------------------------------------------
    # Region Operations
    # ---------------------------------------------------------

    def set_region(self, region: CaptureRegion) -> None:
        """
        Set the active capture region.
        """
        self._validate(region)
        self._region = region
        self._notify()

    def clear(self) -> None:
        """
        Clear the active region.
        """
        self._region = None
        self._notify()

    def update_rectangle(
        self,
        rectangle: Rectangle,
    ) -> None:
        """
        Replace only the rectangle of the current region.
        """
        if self._region is None:
            raise RuntimeError("No active region.")

        self._region = self._region.replace_rectangle(rectangle)
        self._notify()

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def _validate(
        self,
        region: CaptureRegion,
    ) -> None:
        if region.width <= 0:
            raise ValueError("Region width must be positive.")

        if region.height <= 0:
            raise ValueError("Region height must be positive.")

    # ---------------------------------------------------------
    # Event Listeners
    # ---------------------------------------------------------

    def add_listener(
        self,
        listener: RegionListener,
    ) -> None:
        """
        Register a region change listener.
        """
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(
        self,
        listener: RegionListener,
    ) -> None:
        """
        Remove a registered listener.
        """
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify(self) -> None:
        """
        Notify listeners of a region change.
        """
        for listener in tuple(self._listeners):
            listener(self._region)