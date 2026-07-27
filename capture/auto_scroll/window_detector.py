"""
ScrollSnap
==========

Window Detector

Platform-independent window discovery and analysis interface.

Responsibilities
----------------
- Discover the target window
- Track window geometry
- Validate visibility
- Determine whether a point belongs to the window

Platform-specific implementations belong under:

    platform/windows/
    platform/linux/
    platform/macos/
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from models.rectangle import Rectangle


@dataclass(slots=True)
class WindowInfo:
    """
    Information about a detected window.
    """

    handle: int

    title: str

    class_name: str

    process_name: str

    process_id: int

    bounds: Rectangle

    visible: bool = True

    minimized: bool = False

    maximized: bool = False

    dpi_scale: float = 1.0

    scrollable: bool = True


class WindowDetector(ABC):
    """
    Platform-independent window detector.
    """

    @abstractmethod
    def active_window(self) -> WindowInfo | None:
        """
        Return the currently active window.
        """
        raise NotImplementedError

    @abstractmethod
    def window_from_point(
        self,
        x: int,
        y: int,
    ) -> WindowInfo | None:
        """
        Return the window containing the given screen point.
        """
        raise NotImplementedError

    @abstractmethod
    def window_from_handle(
        self,
        handle: int,
    ) -> WindowInfo | None:
        """
        Return window information by native handle.
        """
        raise NotImplementedError

    @abstractmethod
    def enumerate_windows(
        self,
    ) -> list[WindowInfo]:
        """
        Return all top-level windows.
        """
        raise NotImplementedError

    @abstractmethod
    def refresh(
        self,
        window: WindowInfo,
    ) -> WindowInfo:
        """
        Refresh cached window information.
        """
        raise NotImplementedError

    # ---------------------------------------------------------
    # Convenience Methods
    # ---------------------------------------------------------

    def contains_point(
        self,
        window: WindowInfo,
        x: int,
        y: int,
    ) -> bool:
        """
        Check whether a screen coordinate lies inside the window.
        """

        return window.bounds.contains(x, y)

    def moved(
        self,
        previous: WindowInfo,
        current: WindowInfo,
    ) -> bool:
        """
        Determine whether the window moved.
        """

        return previous.bounds != current.bounds

    def resized(
        self,
        previous: WindowInfo,
        current: WindowInfo,
    ) -> bool:
        """
        Determine whether the window size changed.
        """

        return (
            previous.bounds.width != current.bounds.width
            or previous.bounds.height != current.bounds.height
        )