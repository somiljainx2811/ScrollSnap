"""
ScrollSnap
==========

Multi Monitor Manager

Provides a platform-independent abstraction for detecting and
managing multiple displays.

Platform implementations:

    platform/windows/monitors.py
    platform/linux/monitors.py
    platform/macos/monitors.py


Responsibilities
----------------
- Detect connected displays
- Track monitor geometry
- Find monitor from coordinates
- Normalize screen coordinates

This module does not query hardware directly.
"""


from __future__ import annotations

from abc import ABC, abstractmethod

from dataclasses import dataclass

from models.rectangle import Rectangle


@dataclass(slots=True)
class MonitorInfo:
    """
    Represents a display device.
    """

    id: str

    name: str

    bounds: Rectangle

    primary: bool = False

    dpi_scale: float = 1.0

    refresh_rate: int = 60


class MonitorManager(ABC):
    """
    Abstract monitor manager.
    """

    # ---------------------------------------------------------
    # Discovery
    # ---------------------------------------------------------

    @abstractmethod
    def monitors(
        self,
    ) -> list[MonitorInfo]:
        """
        Return all connected monitors.
        """
        raise NotImplementedError


    @abstractmethod
    def primary_monitor(
        self,
    ) -> MonitorInfo | None:
        """
        Return primary display.
        """
        raise NotImplementedError


    @abstractmethod
    def refresh(
        self,
    ) -> None:
        """
        Refresh monitor information.
        """
        raise NotImplementedError


    # ---------------------------------------------------------
    # Lookup
    # ---------------------------------------------------------

    def monitor_at(
        self,
        x: int,
        y: int,
    ) -> MonitorInfo | None:
        """
        Find display containing a point.
        """

        for monitor in self.monitors():

            if monitor.bounds.contains(
                x,
                y,
            ):
                return monitor

        return None


    def monitor_for_region(
        self,
        region: Rectangle,
    ) -> MonitorInfo | None:
        """
        Find monitor containing the largest part
        of a region.
        """

        best = None

        best_area = 0


        for monitor in self.monitors():

            intersection = (
                monitor.bounds
                .intersection(region)
            )

            if intersection:

                area = (
                    intersection.width
                    *
                    intersection.height
                )

                if area > best_area:

                    best_area = area
                    best = monitor


        return best


    # ---------------------------------------------------------
    # Coordinate Conversion
    # ---------------------------------------------------------

    def normalize_point(
        self,
        x: int,
        y: int,
    ) -> tuple[int, int]:
        """
        Convert absolute coordinates into
        normalized virtual-screen coordinates.
        """

        return (
            x,
            y,
        )