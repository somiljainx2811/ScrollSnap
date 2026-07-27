"""
ScrollSnap
==========

Scroll Detector

Determines whether scrolling has actually occurred between two
captured frames.

This module performs lightweight analysis only.

Heavy image processing belongs to the stitching subsystem.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from models.frame import Frame


@dataclass(slots=True)
class ScrollAnalysis:
    """
    Result of analyzing two consecutive frames.
    """

    moved: bool

    estimated_offset: int

    overlap_ratio: float

    duplicate: bool

    confidence: float


class ScrollDetector:
    """
    Detects whether scrolling succeeded.

    The implementation intentionally remains lightweight.

    Future versions may use feature matching,
    optical flow or phase correlation.
    """

    def __init__(
        self,
        movement_threshold: int = 5,
    ) -> None:

        self._threshold = movement_threshold

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def analyze(
        self,
        previous: Frame | None,
        current: Frame,
    ) -> ScrollAnalysis:
        """
        Analyze two frames.

        Parameters
        ----------
        previous
            Previous captured frame.

        current
            Current captured frame.

        Returns
        -------
        ScrollAnalysis
        """

        if previous is None:
            return ScrollAnalysis(
                moved=True,
                estimated_offset=0,
                overlap_ratio=0.0,
                duplicate=False,
                confidence=1.0,
            )

        offset = self._estimate_offset(
            previous.image,
            current.image,
        )

        moved = abs(offset) >= self._threshold

        duplicate = not moved

        overlap = self._estimate_overlap(
            offset,
            current,
        )

        confidence = self._estimate_confidence(
            moved,
            overlap,
        )

        return ScrollAnalysis(
            moved=moved,
            estimated_offset=offset,
            overlap_ratio=overlap,
            duplicate=duplicate,
            confidence=confidence,
        )

    # ---------------------------------------------------------
    # Internal Algorithms
    # ---------------------------------------------------------

    def _estimate_offset(
        self,
        previous: Any,
        current: Any,
    ) -> int:
        """
        Estimate scroll distance.

        Placeholder implementation.

        Real implementation will use
        phase correlation or feature matching.
        """

        return 10

    def _estimate_overlap(
        self,
        offset: int,
        frame: Frame,
    ) -> float:
        """
        Estimate overlap ratio.
        """

        if frame.height == 0:
            return 0.0

        overlap = (
            frame.height - abs(offset)
        ) / frame.height

        return max(
            0.0,
            min(
                1.0,
                overlap,
            ),
        )

    def _estimate_confidence(
        self,
        moved: bool,
        overlap: float,
    ) -> float:
        """
        Estimate confidence score.
        """

        score = 0.5

        if moved:
            score += 0.3

        score += overlap * 0.2

        return max(
            0.0,
            min(
                1.0,
                score,
            ),
        )