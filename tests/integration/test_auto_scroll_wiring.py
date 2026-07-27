"""
Regression test: `CaptureController` used to fabricate a fake
`ScrollAnalysis(moved=True, confidence=0.5, ...)` on every frame
instead of actually comparing consecutive frames, which meant
auto-scroll's end-of-page detection could never trigger for real.
"""

from __future__ import annotations

from tests.conftest import requires_display


@requires_display
class TestCaptureControllerRealScrollDetection:

    def test_scroll_detector_is_real_pillow_backed(self):

        from controllers.capture_controller import CaptureController
        from image_processing.pillow_backend import PillowScrollDetector

        controller = CaptureController()

        try:

            controller._build_auto_scroll_engine("Mouse Wheel")

            assert isinstance(
                controller._scroll_detector, PillowScrollDetector
            )

        finally:
            controller.shutdown()

    def test_previous_frame_tracked_across_captures(self):

        from controllers.capture_controller import CaptureController
        from models.rectangle import Rectangle

        controller = CaptureController()

        try:

            controller.select_region(Rectangle.from_xywh(0, 0, 200, 150))

            assert controller._previous_captured_frame is None

            frame1 = controller.snap()

            controller._on_frame_captured(frame1)

            assert controller._previous_captured_frame is frame1

            frame2 = controller.snap()

            controller._on_frame_captured(frame2)

            assert controller._previous_captured_frame is frame2

        finally:
            controller.shutdown()

    def test_start_capture_resets_previous_frame(self):

        from controllers.capture_controller import CaptureController
        from models.rectangle import Rectangle

        controller = CaptureController()

        try:

            controller.select_region(Rectangle.from_xywh(0, 0, 200, 150))

            frame = controller.snap()

            controller._on_frame_captured(frame)

            assert controller._previous_captured_frame is not None

            controller.start_capture(interval_seconds=5.0)

            assert controller._previous_captured_frame is None

            controller.stop_capture()

        finally:
            controller.shutdown()
