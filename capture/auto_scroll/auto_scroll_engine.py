"""
ScrollSnap
==========

Auto Scroll Engine

Coordinates automatic scrolling.

Responsibilities
----------------
- Execute scroll operations
- Wait for rendering
- Verify scrolling occurred
- Detect end of content
- Adapt scrolling speed
- Recover from failed scrolls

This module does NOT capture screenshots. It only manages scrolling.
"""

from __future__ import annotations

from enum import Enum, auto

from .end_detector import EndDetector
from .scroll_detector import ScrollAnalysis, ScrollDetector
from .scroll_strategies import (
    InputController,
    ScrollRequest,
    ScrollStrategy,
)
from .smart_timing import StabilityWaiter
from .timing import FrameRateLimiter


class AutoScrollState(Enum):
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    FINISHED = auto()
    FAILED = auto()


class AutoScrollEngine:
    """
    Controls automatic scrolling.
    """

    def __init__(
        self,
        strategy: ScrollStrategy,
        controller: InputController,
        detector: ScrollDetector,
        end_detector: EndDetector,
        limiter: FrameRateLimiter,
        stability_waiter: StabilityWaiter | None = None,
        move_to_target: callable | None = None,
    ) -> None:

        self._strategy = strategy
        self._controller = controller
        self._detector = detector
        self._end_detector = end_detector
        self._limiter = limiter
        self._stability_waiter = stability_waiter

        self._move_to_target = move_to_target

        self._state = AutoScrollState.IDLE

        self._scrolls = 0
        self._failures = 0

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def state(self) -> AutoScrollState:
        return self._state

    @property
    def running(self) -> bool:
        return self._state == AutoScrollState.RUNNING

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def start(self) -> None:

        self._state = AutoScrollState.RUNNING

        self._scrolls = 0

        self._failures = 0

        self._end_detector.reset()

        self._limiter.reset()

    def stop(self) -> None:

        self._state = AutoScrollState.FINISHED

    def pause(self) -> None:

        if self.running:
            self._state = AutoScrollState.PAUSED

    def resume(self) -> None:

        if self._state == AutoScrollState.PAUSED:
            self._state = AutoScrollState.RUNNING

    # ---------------------------------------------------------
    # Scroll Cycle
    # ---------------------------------------------------------

    def step(
        self,
        request: ScrollRequest,
        analysis: ScrollAnalysis,
    ) -> bool:
        """
        Perform one auto-scroll cycle.

        Returns False when scrolling should stop.
        """

        if not self.running:
            return False

        end = self._end_detector.analyze(
            analysis,
        )

        if end.reached_end:
            self.stop()
            return False

        if self._move_to_target is not None:
            self._move_to_target()

        self._strategy.scroll(
            self._controller,
            request,
        )

        self._scrolls += 1

        if self._stability_waiter is not None:
            self._stability_waiter.wait()
        else:
            self._limiter.wait()

        return True

    @property
    def last_wait_time(self) -> float | None:
        """
        How long the most recent scroll's stability wait actually
        took, if smart timing is enabled.
        """

        if self._stability_waiter is None:
            return None

        return self._stability_waiter.last_wait_time

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    @property
    def scroll_count(self) -> int:
        return self._scrolls

    @property
    def failure_count(self) -> int:
        return self._failures

    def register_failure(self) -> None:

        self._failures += 1

        if self._failures >= 5:
            self._state = AutoScrollState.FAILED