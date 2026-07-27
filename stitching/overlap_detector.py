"""
ScrollSnap
==========

Overlap Detector

Finds the shared area between consecutive captured frames.

Used by:
    stitching/alignment.py

The detector should answer:

"How many pixels of Frame A are repeated in Frame B?"
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from dataclasses import dataclass

from models.frame import Frame


@dataclass(slots=True)
class OverlapResult:
    """
    Result of overlap detection.
    """

    found: bool

    offset_y: int

    offset_x: int

    overlap_height: int

    overlap_width: int

    confidence: float


class OverlapDetector(ABC):
    """
    Base overlap detector.
    """

    @abstractmethod
    def detect(
        self,
        previous: Frame,
        current: Frame,
    ) -> OverlapResult:
        raise NotImplementedError



class SimpleOverlapDetector(OverlapDetector):
    """
    Lightweight overlap detector.

    Designed as a fallback implementation.

    Future versions can replace this with:
    - feature matching
    - phase correlation
    - optical flow
    """

    def __init__(
        self,
        minimum_overlap: float = 0.15,
        maximum_overlap: float = 0.90,
    ) -> None:

        self.minimum_overlap = minimum_overlap

        self.maximum_overlap = maximum_overlap


    def detect(
        self,
        previous: Frame,
        current: Frame,
    ) -> OverlapResult:

        """
        Estimate vertical scrolling overlap.

        Initial implementation assumes:
        - vertical scrolling
        - same width
        - sequential captures
        """

        height = min(
            previous.height,
            current.height,
        )

        width = min(
            previous.width,
            current.width,
        )


        estimated_overlap = int(
            height * 0.50
        )


        return OverlapResult(

            found=True,

            offset_y=(
                height -
                estimated_overlap
            ),

            offset_x=0,

            overlap_height=(
                estimated_overlap
            ),

            overlap_width=(
                width
            ),

            confidence=0.5,
        )