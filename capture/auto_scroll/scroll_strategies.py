"""
ScrollSnap
==========

Scroll Strategies

Defines platform-independent scrolling strategies used by the
AutoScrollEngine.

Each strategy performs one logical scroll step. The actual OS-specific
input injection is delegated to the InputController interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto


class ScrollDirection(Enum):
    """
    Scroll direction.
    """

    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()


@dataclass(slots=True)
class ScrollRequest:
    """
    Represents one logical scroll operation.
    """

    direction: ScrollDirection = ScrollDirection.DOWN

    amount: int = 3

    smooth: bool = True


class InputController(ABC):
    """
    Abstract interface used to inject user input.

    Concrete implementations belong in:

        capture/input/
    """

    @abstractmethod
    def scroll_wheel(
        self,
        direction: ScrollDirection,
        amount: int,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def press_key(
        self,
        key: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def drag_scrollbar(
        self,
        pixels: int,
    ) -> None:
        raise NotImplementedError


class ScrollStrategy(ABC):
    """
    Base class for every scrolling strategy.
    """

    name = "Base"

    @abstractmethod
    def scroll(
        self,
        controller: InputController,
        request: ScrollRequest,
    ) -> None:
        raise NotImplementedError


class MouseWheelStrategy(ScrollStrategy):
    """
    Standard mouse wheel scrolling.
    """

    name = "Mouse Wheel"

    def scroll(
        self,
        controller: InputController,
        request: ScrollRequest,
    ) -> None:

        controller.scroll_wheel(
            request.direction,
            request.amount,
        )


class KeyboardStrategy(ScrollStrategy):
    """
    Arrow/PageUp/PageDown based scrolling.
    """

    name = "Keyboard"

    def scroll(
        self,
        controller: InputController,
        request: ScrollRequest,
    ) -> None:

        if request.direction == ScrollDirection.DOWN:
            controller.press_key("pagedown")

        elif request.direction == ScrollDirection.UP:
            controller.press_key("pageup")

        elif request.direction == ScrollDirection.LEFT:
            controller.press_key("left")

        elif request.direction == ScrollDirection.RIGHT:
            controller.press_key("right")


class ScrollbarDragStrategy(ScrollStrategy):
    """
    Drag the scrollbar directly.
    """

    name = "Scrollbar"

    def scroll(
        self,
        controller: InputController,
        request: ScrollRequest,
    ) -> None:

        pixels = request.amount * 40

        if request.direction == ScrollDirection.UP:
            pixels *= -1

        controller.drag_scrollbar(
            pixels,
        )


class StrategyRegistry:
    """
    Registry of available scrolling strategies.
    """

    def __init__(self) -> None:

        self._strategies: dict[str, ScrollStrategy] = {}

        self.register(MouseWheelStrategy())
        self.register(KeyboardStrategy())
        self.register(ScrollbarDragStrategy())

    def register(
        self,
        strategy: ScrollStrategy,
    ) -> None:

        self._strategies[strategy.name] = strategy

    def unregister(
        self,
        name: str,
    ) -> None:

        self._strategies.pop(name, None)

    def get(
        self,
        name: str,
    ) -> ScrollStrategy:

        if name not in self._strategies:
            raise KeyError(
                f"Unknown strategy: {name}"
            )

        return self._strategies[name]

    def names(
        self,
    ) -> list[str]:

        return sorted(self._strategies.keys())


default_registry = StrategyRegistry()