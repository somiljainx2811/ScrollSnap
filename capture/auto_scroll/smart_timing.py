"""
ScrollSnap
==========

Smart Capture Timing

Waits for the page to actually finish rendering after a scroll,
instead of a fixed delay:

    Old behavior (still the default without this):
        scroll -> sleep(fixed_interval) -> capture

    Smart behavior (this module):
        scroll -> probe screen every ~60ms -> capture as soon as
        two consecutive probes look the same (rendering settled)
        -> or give up and capture anyway after `max_wait`

This fixes two real problems with a fixed delay: it's too slow
for pages that render instantly (wasting time every single
scroll), and too fast for pages with lazy-loaded images or
animated transitions (capturing a half-rendered frame).

This was called out explicitly in ScrollSnap's original roadmap
("Smart Capture Timing... instead of sleep(1), wait until the
image actually changes") but was never implemented - capture
always used a fixed interval. It's a natural companion to the
real scroll-detection fix, since both rely on the same idea:
actually looking at the screen instead of guessing.
"""

from __future__ import annotations

import time
from typing import Any, Callable


class StabilityWaiter:
    """
    Polls a cheap "probe" callback until two consecutive probes
    are visually stable, or a maximum wait time elapses.
    """

    def __init__(
        self,
        probe: Callable[[], Any],
        is_stable: Callable[[Any, Any], bool],
        max_wait: float = 2.0,
        poll_interval: float = 0.06,
        required_stable_checks: int = 2,
    ) -> None:

        if max_wait <= 0:
            raise ValueError("max_wait must be positive.")

        if poll_interval <= 0:
            raise ValueError("poll_interval must be positive.")

        self._probe = probe

        self._is_stable = is_stable

        self.max_wait = max_wait

        self.poll_interval = poll_interval

        self.required_stable_checks = max(1, required_stable_checks)

        self._last_wait_time = 0.0

    @property
    def last_wait_time(self) -> float:
        """How long the most recent `wait()` call actually took."""

        return self._last_wait_time

    def wait(self) -> bool:
        """
        Block until rendering appears to have stabilized.

        Returns True if stability was detected, False if
        `max_wait` was reached first (the caller should still
        proceed with a capture either way - this is a best-effort
        optimization, not a hard guarantee).
        """

        start = time.perf_counter()

        previous = self._safe_probe()

        stable_count = 0

        stabilized = False

        if previous is not None:

            while time.perf_counter() - start < self.max_wait:

                time.sleep(self.poll_interval)

                current = self._safe_probe()

                if current is None:
                    continue

                if self._is_stable(previous, current):

                    stable_count += 1

                    if stable_count >= self.required_stable_checks:
                        stabilized = True
                        break

                else:
                    stable_count = 0

                previous = current

        self._last_wait_time = time.perf_counter() - start

        return stabilized

    def _safe_probe(self) -> Any:
        """
        Probing touches the real screen/OS - never let a
        transient failure (e.g. a monitor briefly unavailable)
        crash the capture session.
        """

        try:
            return self._probe()

        except Exception:
            return None
