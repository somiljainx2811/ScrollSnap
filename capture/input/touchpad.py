"""
ScrollSnap
==========

Touchpad Input Controller

Provides a platform-independent touchpad gesture abstraction.

Platform implementations:

    platform/windows/touchpad.py
    platform/linux/touchpad.py
    platform/macos/touchpad.py

Responsibilities:
- Gesture scrolling
- Two-finger scrolling
- Swipe gestures
- Pinch/zoom abstraction

This module does not implement hardware interaction.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from capture.auto_scroll.scroll_strategies import (
    ScrollDirection,
)


class TouchpadController(ABC):
    """
    Abstract touchpad controller.
    """

    # ---------------------------------------------------------
    # Scrolling Gestures
    # ---------------------------------------------------------

    @abstractmethod
    def scroll(
        self,
        direction: ScrollDirection,
        amount: float,
        smooth: bool = True,
    ) -> None:
        """
        Perform a touchpad scroll gesture.

        Parameters
        ----------
        direction:
            Scroll direction.

        amount:
            Gesture distance.

        smooth:
            Whether to simulate natural scrolling.
        """
        raise NotImplementedError


    @abstractmethod
    def swipe(
        self,
        direction: ScrollDirection,
        distance: float,
        duration: float = 0.3,
    ) -> None:
        """
        Perform swipe gesture.
        """
        raise NotImplementedError


    @abstractmethod
    def pinch(
        self,
        scale: float,
    ) -> None:
        """
        Perform pinch zoom.

        scale:
            >1 zoom in
            <1 zoom out
        """
        raise NotImplementedError


    # ---------------------------------------------------------
    # Convenience Methods
    # ---------------------------------------------------------

    def scroll_down(
        self,
        amount: float = 5.0,
    ) -> None:
        """
        Scroll downward.
        """

        self.scroll(
            ScrollDirection.DOWN,
            amount,
        )


    def scroll_up(
        self,
        amount: float = 5.0,
    ) -> None:
        """
        Scroll upward.
        """

        self.scroll(
            ScrollDirection.UP,
            amount,
        )


    def smooth_scroll(
        self,
        direction: ScrollDirection,
        amount: float,
    ) -> None:
        """
        Natural scrolling helper.
        """

        self.scroll(
            direction,
            amount,
            smooth=True,
        )