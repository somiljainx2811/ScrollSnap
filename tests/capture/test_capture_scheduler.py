"""
Tests for capture.capture_scheduler.CaptureScheduler.

Includes a regression test for a real threading bug: calling
`stop()` from *within* the scheduler's own callback (which now
happens for real once end-detection actually triggers an
auto-stop - see `tests/stitching/test_alignment.py`'s end-
detection regression test) used to raise
`RuntimeError: cannot join current thread`.
"""

from __future__ import annotations

import time

from capture.capture_scheduler import CaptureScheduler


class TestCaptureScheduler:

    def test_start_and_stop(self):

        calls = []

        scheduler = CaptureScheduler()

        scheduler.set_interval(0.05)

        scheduler.start(lambda: calls.append(1))

        time.sleep(0.22)

        scheduler.stop()

        assert len(calls) >= 2

        assert not scheduler.running

    def test_pause_resume(self):

        calls = []

        scheduler = CaptureScheduler()

        scheduler.set_interval(0.05)

        scheduler.start(lambda: calls.append(1))

        time.sleep(0.12)

        scheduler.pause()

        count_after_pause = len(calls)

        time.sleep(0.15)

        assert len(calls) == count_after_pause  # no calls while paused

        scheduler.resume()

        time.sleep(0.12)

        assert len(calls) > count_after_pause

        scheduler.stop()

    def test_invalid_interval_rejected(self):

        import pytest

        scheduler = CaptureScheduler()

        with pytest.raises(ValueError):
            scheduler.set_interval(0)

        with pytest.raises(ValueError):
            scheduler.set_interval(-1)


class TestSelfStopFromWithinCallbackRegression:
    """
    Regression test: a callback that calls `scheduler.stop()`
    from *inside itself* (i.e. running on the scheduler's own
    background thread) used to crash with
    `RuntimeError: cannot join current thread`.
    """

    def test_callback_can_stop_its_own_scheduler(self):

        scheduler = CaptureScheduler()

        scheduler.set_interval(0.03)

        errors: list[Exception] = []

        call_count = {"value": 0}

        def self_stopping_callback():

            call_count["value"] += 1

            try:
                scheduler.stop()  # called from the scheduler's own thread

            except Exception as exc:  # pragma: no cover - the bug
                errors.append(exc)

        scheduler.start(self_stopping_callback)

        time.sleep(0.3)

        assert errors == [], f"stop() raised from within itself: {errors}"

        assert call_count["value"] >= 1

        assert not scheduler.running
