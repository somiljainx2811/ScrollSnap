"""
ScrollSnap
==========

Capture Scheduler

Coordinates timed capture operations.

The scheduler does not perform screen captures itself.
Instead, it periodically invokes a callback supplied by the
capture engine.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable


CaptureCallback = Callable[[], None]


class CaptureScheduler:
    """
    Schedules repeated capture callbacks.
    """

    def __init__(self) -> None:

        self._interval = 0.5

        self._running = False

        self._paused = False

        self._thread: threading.Thread | None = None

        self._callback: CaptureCallback | None = None

        self._on_error: Callable[[Exception], None] | None = None

    # ---------------------------------------------------------
    # Configuration
    # ---------------------------------------------------------

    @property
    def interval(self) -> float:
        return self._interval

    def set_interval(
        self,
        seconds: float,
    ) -> None:

        if seconds <= 0:
            raise ValueError(
                "Interval must be positive."
            )

        self._interval = seconds

    # ---------------------------------------------------------
    # State
    # ---------------------------------------------------------

    @property
    def running(self) -> bool:
        return self._running

    @property
    def paused(self) -> bool:
        return self._paused

    # ---------------------------------------------------------
    # Control
    # ---------------------------------------------------------

    def start(
        self,
        callback: CaptureCallback,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        """
        Begin periodic callbacks.

        `on_error`, if given, is invoked (from the background
        capture thread) if `callback` ever raises. The scheduler
        stops itself before calling it, so it never spins on a
        broken capture callback.
        """

        if self._running:
            return

        self._callback = callback

        self._on_error = on_error

        self._running = True

        self._paused = False

        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
        )

        self._thread.start()

    def stop(self) -> None:
        """
        Stop scheduler.
        """

        self._running = False

        if (
            self._thread is not None
            and self._thread.is_alive()
            and threading.current_thread() is not self._thread
        ):
            self._thread.join(timeout=1)

        self._thread = None

    def pause(self) -> None:

        self._paused = True

    def resume(self) -> None:

        self._paused = False

    # ---------------------------------------------------------
    # Internal Loop
    # ---------------------------------------------------------

    def _run(self) -> None:

        while self._running:

            if self._paused:
                time.sleep(0.05)
                continue

            start = time.perf_counter()

            if self._callback is not None:

                try:
                    self._callback()

                except Exception as exc:  # noqa: BLE001

                    self._running = False

                    if self._on_error is not None:
                        self._on_error(exc)

                    return

            elapsed = time.perf_counter() - start

            delay = self._interval - elapsed

            if delay > 0:
                time.sleep(delay)