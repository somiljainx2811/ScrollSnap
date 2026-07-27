"""
ScrollSnap
==========

Alignment Engine

Calculates placement offsets between captured frames.

Responsibilities:
- Convert overlap information into coordinates
- Maintain cumulative canvas position
- Support vertical and horizontal scrolling

Does NOT:
- Compare images
- Blend pixels
- Remove duplicates
"""

from __future__ import annotations

from dataclasses import dataclass

from .overlap_detector import OverlapResult

from models.frame import Frame



@dataclass(slots=True)
class FrameAlignment:
    """
    Position of a frame in the final stitched image.
    """

    frame_index: int

    x: int

    y: int

    width: int

    height: int

    confidence: float



class AlignmentEngine:
    """
    Calculates frame placement.
    """

    def __init__(
        self,
    ) -> None:

        self.reset()


    # ---------------------------------------------------------
    # State
    # ---------------------------------------------------------

    def reset(
        self,
    ) -> None:

        self._current_x = 0

        self._current_y = 0

        self._index = 0



    # ---------------------------------------------------------
    # Alignment
    # ---------------------------------------------------------

    def calculate(
        self,
        overlap: OverlapResult,
    ) -> FrameAlignment:
        """
        Calculate next frame position.
        """

        self._current_y += (
            overlap.offset_y
        )


        self._index += 1


        return FrameAlignment(

            frame_index=self._index,

            x=self._current_x,

            y=self._current_y,

            width=overlap.overlap_width,

            height=overlap.overlap_height,

            confidence=overlap.confidence,
        )



    def align_sequence(
        self,
        frames: list[Frame],
        overlaps: list[OverlapResult],
    ) -> list[FrameAlignment]:
        """
        Align complete frame sequence.
        """

        self.reset()


        result = [

            FrameAlignment(
                frame_index=0,
                x=0,
                y=0,
                width=frames[0].width,
                height=frames[0].height,
                confidence=1.0,
            )

        ]


        for overlap in overlaps:

            result.append(
                self.calculate(
                    overlap
                )
            )


        return result