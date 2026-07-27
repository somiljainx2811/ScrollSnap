"""
ScrollSnap
==========

Pynput Input Backend

Concrete, cross-platform implementations of:

    capture.input.mouse.MouseController
    capture.input.touchpad.TouchpadController
    capture.auto_scroll.scroll_strategies.InputController

built on top of `pynput`, which already abstracts Windows,
macOS, and X11/Linux input injection behind one API.
"""

from __future__ import annotations

import time

from pynput.keyboard import Controller as PynputKeyboard
from pynput.keyboard import Key
from pynput.mouse import Button as PynputButton
from pynput.mouse import Controller as PynputMouse

from capture.auto_scroll.scroll_strategies import (
    InputController,
    ScrollDirection,
)
from capture.input.mouse import MouseController
from capture.input.touchpad import TouchpadController


_BUTTONS = {
    "left": PynputButton.left,
    "right": PynputButton.right,
    "middle": PynputButton.middle,
}

# pynput scroll() dy is positive = scroll up (content moves down).
_DIRECTION_VECTORS = {
    ScrollDirection.UP: (0, 1),
    ScrollDirection.DOWN: (0, -1),
    ScrollDirection.LEFT: (-1, 0),
    ScrollDirection.RIGHT: (1, 0),
}

_ARROW_KEYS = {
    ScrollDirection.UP: Key.up,
    ScrollDirection.DOWN: Key.down,
    ScrollDirection.LEFT: Key.left,
    ScrollDirection.RIGHT: Key.right,
}

_NAMED_KEYS = {
    "pagedown": Key.page_down,
    "pageup": Key.page_up,
    "up": Key.up,
    "down": Key.down,
    "left": Key.left,
    "right": Key.right,
    "space": Key.space,
    "home": Key.home,
    "end": Key.end,
    "escape": Key.esc,
    "enter": Key.enter,
    "tab": Key.tab,
}


class PynputMouseController(MouseController):
    """
    Concrete `MouseController` using `pynput`.
    """

    def __init__(self) -> None:
        self._mouse = PynputMouse()

    def move(self, x: int, y: int) -> None:
        self._mouse.position = (x, y)

    def position(self) -> tuple[int, int]:
        return self._mouse.position

    def press(self, button: str = "left") -> None:
        self._mouse.press(_BUTTONS[button])

    def release(self, button: str = "left") -> None:
        self._mouse.release(_BUTTONS[button])

    def click(self, button: str = "left") -> None:
        self._mouse.click(_BUTTONS[button])

    def scroll(
        self,
        direction: ScrollDirection,
        amount: int,
    ) -> None:

        dx, dy = _DIRECTION_VECTORS[direction]

        self._mouse.scroll(dx * amount, dy * amount)


class PynputTouchpadController(TouchpadController):
    """
    Concrete `TouchpadController`.

    `pynput` has no native touchpad/gesture API, so gestures are
    approximated as a burst of small, evenly spaced scroll
    events, which produces a visually similar smooth-scrolling
    effect on most applications.
    """

    def __init__(self, step_delay: float = 0.008) -> None:

        self._mouse = PynputMouse()

        self._step_delay = step_delay

    def scroll(
        self,
        direction: ScrollDirection,
        amount: float,
        smooth: bool = True,
    ) -> None:

        dx, dy = _DIRECTION_VECTORS[direction]

        if not smooth:
            self._mouse.scroll(
                int(dx * amount), int(dy * amount)
            )
            return

        steps = max(1, int(amount))

        for _ in range(steps):

            self._mouse.scroll(dx, dy)

            time.sleep(self._step_delay)

    def swipe(
        self,
        direction: ScrollDirection,
        distance: float,
        duration: float = 0.3,
    ) -> None:

        steps = max(1, int(distance))

        delay = duration / steps

        dx, dy = _DIRECTION_VECTORS[direction]

        for _ in range(steps):

            self._mouse.scroll(dx, dy)

            time.sleep(delay)

    def pinch(self, scale: float) -> None:
        """
        Not meaningfully expressible as discrete input events;
        no-op on this backend.
        """

        return None


class PynputInputController(InputController):
    """
    Concrete `InputController` used by `AutoScrollEngine`.

    Wraps a `PynputMouseController` + `pynput` keyboard for the
    three operations the scroll strategies need.
    """

    def __init__(
        self,
        mouse: PynputMouseController | None = None,
    ) -> None:

        self._mouse = mouse or PynputMouseController()

        self._keyboard = PynputKeyboard()

    def scroll_wheel(
        self,
        direction: ScrollDirection,
        amount: int,
    ) -> None:

        self._mouse.scroll(direction, amount)

    def press_key(self, key: str) -> None:

        mapped = _NAMED_KEYS.get(key.lower())

        target = mapped if mapped is not None else key

        self._keyboard.press(target)

        self._keyboard.release(target)

    def drag_scrollbar(self, pixels: int) -> None:
        """
        Drags the scrollbar at the current cursor's x position
        downward/upward by `pixels`. Callers are expected to
        have already positioned the cursor over the scrollbar
        thumb (the region manager / window detector supplies
        that geometry).
        """

        x, y = self._mouse.position()

        self._mouse.press("left")

        self._mouse.move(x, y + pixels)

        self._mouse.release("left")
