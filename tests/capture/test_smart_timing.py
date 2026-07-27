"""
Tests for the new "smart capture timing" feature:
`capture.auto_scroll.smart_timing.StabilityWaiter`, and its
wiring into `AutoScrollEngine` / `CaptureController`.
"""

from __future__ import annotations

import time

from capture.auto_scroll.smart_timing import StabilityWaiter
from image_processing.alignment import (
    images_visually_stable,
    quick_fingerprint,
)
from tests.conftest import requires_display


class TestStabilityWaiter:

    def test_returns_true_when_probe_never_changes(self):

        waiter = StabilityWaiter(
            probe=lambda: "same",
            is_stable=lambda a, b: a == b,
            max_wait=1.0,
            poll_interval=0.02,
            required_stable_checks=2,
        )

        assert waiter.wait() is True

        assert waiter.last_wait_time < 1.0

    def test_returns_false_on_timeout_if_never_stable(self):

        waiter = StabilityWaiter(
            probe=lambda: time.perf_counter(),  # always "different"
            is_stable=lambda a, b: False,
            max_wait=0.2,
            poll_interval=0.02,
        )

        assert waiter.wait() is False

        assert waiter.last_wait_time >= 0.2

    def test_survives_probe_exceptions(self):

        def flaky_probe():
            raise RuntimeError("transient failure")

        waiter = StabilityWaiter(
            probe=flaky_probe,
            is_stable=lambda a, b: True,
            max_wait=0.2,
            poll_interval=0.02,
        )

        # Must not raise, even though every probe fails.
        result = waiter.wait()

        assert result is False

    def test_rejects_invalid_config(self):

        import pytest

        with pytest.raises(ValueError):
            StabilityWaiter(lambda: None, lambda a, b: True, max_wait=0)

        with pytest.raises(ValueError):
            StabilityWaiter(
                lambda: None, lambda a, b: True, poll_interval=0
            )


class TestVisualFingerprint:

    def test_identical_images_are_stable(self, solid_image):

        image = solid_image(color=(50, 60, 70))

        fp_a = quick_fingerprint(image)

        fp_b = quick_fingerprint(image.copy())

        assert images_visually_stable(fp_a, fp_b)

    def test_very_different_images_are_not_stable(self, solid_image):

        black = solid_image(color=(0, 0, 0))

        white = solid_image(color=(255, 255, 255))

        fp_a = quick_fingerprint(black)

        fp_b = quick_fingerprint(white)

        assert not images_visually_stable(fp_a, fp_b)


@requires_display
class TestCaptureControllerSmartTiming:

    def test_stability_waiter_probes_real_screen(self):

        from controllers.capture_controller import CaptureController
        from models.rectangle import Rectangle

        controller = CaptureController()

        try:

            controller.select_region(Rectangle.from_xywh(0, 0, 200, 150))

            waiter = controller._build_stability_waiter(max_wait=0.3)

            assert waiter is not None

            stabilized = waiter.wait()

            # A static Xvfb desktop should stabilize almost
            # immediately.
            assert stabilized is True

        finally:
            controller.shutdown()

    def test_no_region_selected_returns_none(self):

        from controllers.capture_controller import CaptureController

        controller = CaptureController()

        try:
            assert controller._build_stability_waiter(1.0) is None

        finally:
            controller.shutdown()

    def test_auto_scroll_engine_receives_stability_waiter(self):

        from controllers.capture_controller import CaptureController
        from models.rectangle import Rectangle

        controller = CaptureController()

        try:

            controller.select_region(Rectangle.from_xywh(0, 0, 200, 150))

            engine = controller._build_auto_scroll_engine(
                "Mouse Wheel", smart_timing=True, max_wait=0.3
            )

            assert engine._stability_waiter is not None

        finally:
            controller.shutdown()

    def test_smart_timing_disabled_falls_back_to_fixed_limiter(self):

        from controllers.capture_controller import CaptureController
        from models.rectangle import Rectangle

        controller = CaptureController()

        try:

            controller.select_region(Rectangle.from_xywh(0, 0, 200, 150))

            engine = controller._build_auto_scroll_engine(
                "Mouse Wheel", smart_timing=False
            )

            assert engine._stability_waiter is None

        finally:
            controller.shutdown()
