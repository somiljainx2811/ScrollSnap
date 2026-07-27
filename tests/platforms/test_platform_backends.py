"""
Live tests for the concrete platform backends (mss screen
capture, pynput input, Linux window detection). These need a
real or virtual (Xvfb) X server, so they're skipped without one.
"""

from __future__ import annotations

from models.rectangle import Rectangle
from tests.conftest import requires_display


@requires_display
class TestMssScreenCapture:

    def test_capture_region_returns_correct_size(self):

        from platforms.screen_capture import MssScreenCapture

        capture = MssScreenCapture()

        image = capture.capture_region(Rectangle.from_xywh(0, 0, 300, 200))

        assert image.size == (300, 200)

        capture.close()

    def test_monitor_count_is_positive(self):

        from platforms.screen_capture import MssScreenCapture

        capture = MssScreenCapture()

        assert capture.monitor_count() >= 1

        capture.close()


@requires_display
class TestPynputInput:

    def test_mouse_move_updates_position(self):

        from platforms.input_controller import PynputMouseController

        mouse = PynputMouseController()

        mouse.move(77, 88)

        assert mouse.position() == (77, 88)

    def test_scroll_does_not_raise(self):

        from capture.auto_scroll.scroll_strategies import ScrollDirection
        from platforms.input_controller import PynputMouseController

        mouse = PynputMouseController()

        mouse.scroll(ScrollDirection.DOWN, 2)  # should not raise


@requires_display
class TestLinuxWindowDetector:

    def test_constructs_without_error(self):

        from platforms.window_detector import LinuxWindowDetector

        LinuxWindowDetector()  # should not raise

    def test_factory_returns_a_detector(self):

        from platforms.window_detector import create_window_detector

        detector = create_window_detector()

        assert detector is not None


@requires_display
class TestPlatformServicesBundle:

    def test_bundle_constructs_every_backend(self):

        from platforms.factory import PlatformServices

        services = PlatformServices()

        assert services.screen_capture is not None

        assert services.mouse is not None

        assert services.input_controller is not None

        assert services.hotkeys is not None

        assert services.window_detector is not None
