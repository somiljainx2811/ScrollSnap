"""
ScrollSnap
==========

Screen Capture Interface

Platform-independent interface for screen capture.

Actual implementations live under:

    platform/windows/
    platform/linux/
    platform/macos/

The capture engine only depends on this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from models.rectangle import Rectangle


class ScreenCapture(ABC):
    """
    Abstract screen capture backend.
    """

    @abstractmethod
    def capture_region(
        self,
        region: Rectangle,
    ):
        """
        Capture a rectangular region.

        Returns
        -------
        Image object

        The concrete image type depends on the selected backend
        (Pillow/OpenCV/etc.).
        """
        raise NotImplementedError

    @abstractmethod
    def capture_monitor(
        self,
        monitor_id: int,
    ):
        """
        Capture an entire monitor.
        """
        raise NotImplementedError

    @abstractmethod
    def capture_window(
        self,
        window_handle: int,
    ):
        """
        Capture a single window.
        """
        raise NotImplementedError

    @abstractmethod
    def monitor_count(self) -> int:
        """
        Number of available monitors.
        """
        raise NotImplementedError

    @abstractmethod
    def monitor_geometry(
        self,
        monitor_id: int,
    ) -> Rectangle:
        """
        Returns monitor bounds.
        """
        raise NotImplementedError