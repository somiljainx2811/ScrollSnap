"""
ScrollSnap
==========

Mouse Input Controller

Provides mouse-based input abstraction.

Responsibilities
----------------
- Mouse movement
- Clicks
- Wheel scrolling
- Drag operations

Platform-specific implementations should subclass this controller.

Example:

platform/windows/mouse.py
platform/linux/mouse.py
platform/macos/mouse.py
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from capture.auto_scroll.scroll_strategies import (
    ScrollDirection,
)


class MouseController(ABC):
    """
    Abstract mouse controller.
    """

    # ---------------------------------------------------------
    # Movement
    # ---------------------------------------------------------

    @abstractmethod
    def move(
        self,
        x: int,
        y: int,
    ) -> None:
        """
        Move cursor to screen coordinates.
        """
        raise NotImplementedError


    @abstractmethod
    def position(
        self,
    ) -> tuple[int, int]:
        """
        Return current cursor position.
        """
        raise NotImplementedError


    # ---------------------------------------------------------
    # Buttons
    # ---------------------------------------------------------

    @abstractmethod
    def press(
        self,
        button: str = "left",
    ) -> None:
        """
        Press mouse button.
        """
        raise NotImplementedError


    @abstractmethod
    def release(
        self,
        button: str = "left",
    ) -> None:
        """
        Release mouse button.
        """
        raise NotImplementedError


    @abstractmethod
    def click(
        self,
        button: str = "left",
    ) -> None:
        """
        Perform click.
        """
        raise NotImplementedError


    # ---------------------------------------------------------
    # Scrolling
    # ---------------------------------------------------------

    @abstractmethod
    def scroll(
        self,
        direction: ScrollDirection,
        amount: int,
    ) -> None:
        """
        Scroll using mouse wheel.
        """
        raise NotImplementedError


    # ---------------------------------------------------------
    # Dragging
    # ---------------------------------------------------------

    def drag(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
        duration: float = 0.5,
    ) -> None:
        """
        Generic drag operation.

        Default implementation uses:
        move -> press -> move -> release
        """

        self.move(
            start[0],
            start[1],
        )

        self.press()

        self.move(
            end[0],
            end[1],
        )

        self.release()