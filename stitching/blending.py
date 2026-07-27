"""
ScrollSnap
==========

Image Blending Engine

Combines aligned frames into a single image.

Responsibilities:
- Place frames on canvas
- Merge overlapping regions
- Apply blending masks

Does NOT:
- Detect overlap
- Calculate alignment
- Export files
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from dataclasses import dataclass

from typing import Any

from .alignment import FrameAlignment

from models.frame import Frame



@dataclass(slots=True)
class Canvas:
    """
    Represents stitching canvas.
    """

    width: int

    height: int

    image: Any = None



class Blender(ABC):
    """
    Base blender interface.
    """

    @abstractmethod
    def merge(
        self,
        frames: list[Frame],
        alignments: list[FrameAlignment],
    ) -> Any:
        raise NotImplementedError



class AlphaBlender(Blender):
    """
    Default alpha blending implementation.

    Overlapping regions are gradually mixed.
    """


    def merge(
        self,
        frames: list[Frame],
        alignments: list[FrameAlignment],
    ) -> Canvas:

        canvas_size = (
            self._calculate_canvas_size(
                frames,
                alignments,
            )
        )


        canvas = Canvas(
            width=canvas_size[0],
            height=canvas_size[1],
        )


        canvas.image = (
            self._create_canvas(
                canvas.width,
                canvas.height,
            )
        )


        for frame, position in zip(
            frames,
            alignments,
        ):

            self._place_frame(
                canvas,
                frame,
                position,
            )


        return canvas



    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _calculate_canvas_size(
        self,
        frames,
        alignments,
    ) -> tuple[int, int]:

        if not frames:
            return (0, 0)

        # The first frame is always placed at the origin and has
        # no corresponding entry in `alignments` (which only
        # covers transitions *between* frames), so it must be
        # accounted for explicitly - otherwise a single-frame (or
        # otherwise alignment-less) list produces a 0x0 canvas.
        width = frames[0].width

        height = frames[0].height

        for frame, position in zip(
            frames[1:],
            alignments,
        ):

            width = max(
                width,
                position.x +
                frame.width,
            )

            height = max(
                height,
                position.y +
                frame.height,
            )


        return (
            width,
            height,
        )



    def _create_canvas(
        self,
        width: int,
        height: int,
    ) -> Any:
        """
        Placeholder canvas creation.

        Actual implementation will depend on
        image backend.
        """

        return {
            "width": width,
            "height": height,
            "pixels": [],
        }



    def _place_frame(
        self,
        canvas: Canvas,
        frame: Frame,
        position: FrameAlignment,
    ) -> None:
        """
        Place frame on canvas.

        Real implementation:
        - alpha masks
        - pixel interpolation
        - seam handling
        """

        pass