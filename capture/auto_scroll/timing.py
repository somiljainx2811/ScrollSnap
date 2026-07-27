"""
ScrollSnap
==========

Auto Scroll Timing

Provides timing utilities used by the auto-scroll engine.

The goal is to produce stable, drift-resistant timing for
automatic scrolling and frame capture.
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(slots=True)
class TimingState:
    """
    Stores scheduler timing information.
    """

    interval: float

    next_tick: float = 0.0

    tick_count: int = 0

    def initialize(self) -> None:
        """
        Initialize the timing state.
        """
        now = time.perf_counter()
        self.next_tick = now + self.interval
        self.tick_count = 0

    def wait(self) -> None:
        """
        Wait until the next scheduled tick.
        """

        while True:
            remaining = self.next_tick - time.perf_counter()

            if remaining <= 0:
                break

            if remaining > 0.002:
                time.sleep(remaining - 0.001)

        self.tick_count += 1
        self.next_tick += self.interval

    def reset(self) -> None:
        """
        Restart timing.
        """
        self.initialize()


class FrameRateLimiter:
    """
    Maintains a fixed execution rate.
    """

    def __init__(
        self,
        interval: float,
    ) -> None:

        if interval <= 0:
            raise ValueError(
                "Interval must be positive."
            )

        self._state = TimingState(interval)
        self._state.initialize()

    @property
    def interval(self) -> float:
        return self._state.interval

    def wait(self) -> None:
        """
        Wait until the next frame.
        """
        self._state.wait()

    def reset(self) -> None:
        """
        Restart the timer.
        """
        self._state.reset()