"""
ScrollSnap
==========

Duplicate Removal

Removes repeated regions between consecutive frames.

Responsibilities:
- Detect repeated frame areas
- Calculate crop boundaries
- Remove duplicated content

Does NOT:
- Align frames
- Blend images
"""

from __future__ import annotations

from dataclasses import dataclass

from models.frame import Frame



@dataclass(slots=True)
class DuplicateRegion:
    """
    Represents duplicated content.
    """

    found: bool

    height: int

    start_y: int

    confidence: float



class DuplicateRemover:
    """
    Removes duplicate scrolling regions.
    """


    def __init__(
        self,
        minimum_match: float = 0.85,
    ) -> None:

        self.minimum_match = (
            minimum_match
        )


    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def detect(
        self,
        previous: Frame,
        current: Frame,
    ) -> DuplicateRegion:
        """
        Detect repeated area.
        """

        overlap_height = self._estimate_overlap(
            previous,
            current,
        )


        confidence = (
            0.9
            if overlap_height > 0
            else 0.0
        )


        return DuplicateRegion(

            found=(
                overlap_height > 0
            ),

            height=overlap_height,

            start_y=0,

            confidence=confidence,
        )


    def remove(
        self,
        frames: list[Frame],
    ) -> list[Frame]:
        """
        Remove duplicate portions.

        Current implementation preserves
        frame order and prepares metadata.

        Actual pixel cropping happens during
        blending.
        """

        if len(frames) <= 1:
            return frames


        cleaned = [
            frames[0]
        ]


        for index in range(
            1,
            len(frames),
        ):

            duplicate = self.detect(
                frames[index - 1],
                frames[index],
            )


            if duplicate.found:

                frames[index].metadata[
                    "duplicate_height"
                ] = duplicate.height


            cleaned.append(
                frames[index]
            )


        return cleaned


    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _estimate_overlap(
        self,
        previous: Frame,
        current: Frame,
    ) -> int:
        """
        Estimate duplicated pixel height.

        Placeholder implementation.

        Future versions:
        - pixel comparison
        - feature matching
        - OCR comparison
        """

        return int(
            min(
                previous.height,
                current.height,
            )
            *
            0.5
        )