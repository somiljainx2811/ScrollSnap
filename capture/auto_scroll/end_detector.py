"""
ScrollSnap
==========

End Detector

Determines whether automatic scrolling has reached the end of the
scrollable content.

This detector uses ScrollAnalysis along with capture history to avoid
false positives caused by temporary stalls or rendering delays.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import deque

from .scroll_detector import ScrollAnalysis


@dataclass(slots=True)
class EndAnalysis:
    """
    Result of end-of-content detection.
    """

    reached_end: bool

    confidence: float

    reason: str

    duplicate_frames: int

    stalled_frames: int


class EndDetector:
    """
    Determines whether scrolling should stop.
    """

    def __init__(
        self,
        duplicate_threshold: int = 3,
        stall_threshold: int = 3,
        confidence_threshold: float = 0.90,
        history_size: int = 10,
    ) -> None:

        self._duplicate_threshold = duplicate_threshold
        self._stall_threshold = stall_threshold
        self._confidence_threshold = confidence_threshold

        self._history: deque[ScrollAnalysis] = deque(
            maxlen=history_size
        )

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def reset(self) -> None:
        """
        Reset detector state.
        """

        self._history.clear()

    def analyze(
        self,
        analysis: ScrollAnalysis,
    ) -> EndAnalysis:
        """
        Analyze the latest scroll result.
        """

        self._history.append(analysis)

        duplicate_count = sum(
            1 for item in self._history if item.duplicate
        )

        stalled_count = sum(
            1 for item in self._history if not item.moved
        )

        reached = (
            duplicate_count >= self._duplicate_threshold
            or stalled_count >= self._stall_threshold
        )

        confidence = self._compute_confidence(
            duplicate_count,
            stalled_count,
        )

        reason = self._determine_reason(
            duplicate_count,
            stalled_count,
            reached,
        )

        return EndAnalysis(
            reached_end=reached,
            confidence=confidence,
            reason=reason,
            duplicate_frames=duplicate_count,
            stalled_frames=stalled_count,
        )

    # ---------------------------------------------------------
    # Internal Helpers
    # ---------------------------------------------------------

    def _compute_confidence(
        self,
        duplicates: int,
        stalls: int,
    ) -> float:

        score = 0.0

        score += min(
            duplicates / self._duplicate_threshold,
            1.0,
        ) * 0.5

        score += min(
            stalls / self._stall_threshold,
            1.0,
        ) * 0.5

        return score

    def _determine_reason(
        self,
        duplicates: int,
        stalls: int,
        reached: bool,
    ) -> str:

        if not reached:
            return "scrolling"

        if duplicates >= self._duplicate_threshold:
            return "duplicate_frames"

        if stalls >= self._stall_threshold:
            return "no_movement"

        return "unknown"