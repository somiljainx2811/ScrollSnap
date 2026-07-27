"""
ScrollSnap
==========

Platform Backend Factory

Single place the rest of the application asks for concrete,
OS-appropriate implementations of every abstract capture/input
interface. Controllers and the UI layer should depend on this
module instead of constructing platform backends directly.
"""

from __future__ import annotations

from capture.auto_scroll.scroll_strategies import InputController
from capture.auto_scroll.window_detector import WindowDetector
from capture.input.hotkeys import HotkeyManager
from capture.input.mouse import MouseController
from capture.screen_capture import ScreenCapture

from platforms.hotkey_manager import PynputHotkeyManager
from platforms.input_controller import (
    PynputInputController,
    PynputMouseController,
    PynputTouchpadController,
)
from platforms.screen_capture import MssScreenCapture
from platforms.window_detector import create_window_detector


def create_screen_capture() -> ScreenCapture:
    return MssScreenCapture()


def create_mouse_controller() -> MouseController:
    return PynputMouseController()


def create_input_controller() -> InputController:
    return PynputInputController()


def create_touchpad_controller() -> PynputTouchpadController:
    return PynputTouchpadController()


def create_hotkey_manager() -> HotkeyManager:
    return PynputHotkeyManager()


def create_window_detector_backend() -> WindowDetector:
    return create_window_detector()


class PlatformServices:
    """
    Convenience bundle of every platform backend the capture
    pipeline needs, constructed once and shared.
    """

    def __init__(self) -> None:

        self.screen_capture: ScreenCapture = create_screen_capture()

        self.mouse: MouseController = create_mouse_controller()

        self.input_controller: InputController = (
            create_input_controller()
        )

        self.touchpad = create_touchpad_controller()

        self.hotkeys: HotkeyManager = create_hotkey_manager()

        self.window_detector: WindowDetector = (
            create_window_detector_backend()
        )

    def __repr__(self) -> str:

        return (
            "PlatformServices("
            f"capture={type(self.screen_capture).__name__}, "
            f"window_detector={type(self.window_detector).__name__}"
            ")"
        )
