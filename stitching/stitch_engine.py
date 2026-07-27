"""
ScrollSnap
==========

Stitch Engine

Coordinates the image stitching pipeline.

Responsibilities
----------------
- Validate frames
- Order frames
- Align frames
- Remove duplicates
- Blend images
- Produce final stitched result


Does NOT:
- Capture screenshots
- Export files
- Modify UI
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from models.frame import Frame


class StitchState(Enum):
    """
    Current stitching state.
    """

    IDLE = auto()
    PREPARING = auto()
    ALIGNING = auto()
    BLENDING = auto()
    COMPLETED = auto()
    FAILED = auto()


@dataclass(slots=True)
class StitchResult:
    """
    Result of stitching operation.
    """

    image: object | None

    frame_count: int

    width: int

    height: int

    success: bool

    error: str | None = None


class StitchEngine:
    """
    Main stitching coordinator.
    """

    def __init__(
        self,
        overlap_detector,
        alignment_engine,
        duplicate_remover,
        blender,
        crop_optimizer,
    ) -> None:

        self._overlap_detector = (
            overlap_detector
        )

        self._alignment = (
            alignment_engine
        )

        self._duplicate_remover = (
            duplicate_remover
        )

        self._blender = blender

        self._crop_optimizer = (
            crop_optimizer
        )

        self._state = StitchState.IDLE


    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def state(
        self,
    ) -> StitchState:

        return self._state


    # ---------------------------------------------------------
    # Pipeline
    # ---------------------------------------------------------

    def stitch(
        self,
        frames: list[Frame],
    ) -> StitchResult:

        try:

            self._state = (
                StitchState.PREPARING
            )

            self._validate(
                frames
            )


            frames = (
                self._duplicate_remover
                .remove(frames)
            )


            self._state = (
                StitchState.ALIGNING
            )


            alignments = (
                self._calculate_alignment(
                    frames
                )
            )


            self._state = (
                StitchState.BLENDING
            )


            image = (
                self._blender.merge(
                    frames,
                    alignments,
                )
            )


            image = (
                self._crop_optimizer
                .optimize(image)
            )


            self._state = (
                StitchState.COMPLETED
            )


            return StitchResult(
                image=image,
                frame_count=len(frames),
                width=getattr(
                    image,
                    "width",
                    0,
                ),
                height=getattr(
                    image,
                    "height",
                    0,
                ),
                success=True,
            )


        except Exception as exc:

            self._state = (
                StitchState.FAILED
            )

            return StitchResult(
                image=None,
                frame_count=0,
                width=0,
                height=0,
                success=False,
                error=str(exc),
            )


    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _validate(
        self,
        frames: list[Frame],
    ) -> None:

        if not frames:
            raise ValueError(
                "No frames available."
            )


    def _calculate_alignment(
        self,
        frames: list[Frame],
    ):

        # `AlignmentEngine` is stateful - it keeps a running
        # `frame_index` and cumulative (x, y) position across
        # calls to `calculate()` so consecutive frames within one
        # stitch stack correctly. But `StitchEngine` is a
        # long-lived object (constructed once per app session, not
        # once per stitch), so without an explicit reset here, a
        # *second* scrolling capture in the same session picks up
        # `frame_index` right where the first one left off -
        # producing indices that overrun the new (usually shorter)
        # `frames` list and blowing up `_placements()` with
        # "list index out of range".
        self._alignment.reset()

        result = []

        for index in range(
            len(frames) - 1
        ):

            overlap = (
                self._overlap_detector
                .detect(
                    frames[index],
                    frames[index + 1],
                )
            )

            alignment = (
                self._alignment
                .calculate(
                    overlap
                )
            )

            result.append(
                alignment
            )

        return result