"""
ScrollSnap
==========

Rectangle Shape

Default capture shape.

Supports:
- Position
- Resize
- Point containment
- Area calculation
- Mask generation
"""

from __future__ import annotations

from dataclasses import dataclass

from typing import Any

from .base_shape import (
    Shape,
    ShapeBounds,
)



@dataclass(slots=True)
class RectangleConfig:
    """
    Rectangle configuration.
    """

    x: int

    y: int

    width: int

    height: int



class RectangleShape(Shape):
    """
    Standard rectangular capture region.
    """


    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> None:

        super().__init__()

        self.x = x

        self.y = y

        self.width = width

        self.height = height



    # ---------------------------------------------------------
    # Geometry
    # ---------------------------------------------------------

    def contains(
        self,
        x: int,
        y: int,
    ) -> bool:
        """
        Check if point is inside rectangle.
        """

        return (
            self.x <= x <=
            self.x + self.width
            and
            self.y <= y <=
            self.y + self.height
        )



    def bounds(
        self,
    ) -> ShapeBounds:

        return ShapeBounds(

            x=self.x,

            y=self.y,

            width=self.width,

            height=self.height,
        )



    def area(
        self,
    ) -> float:

        return (
            self.width *
            self.height
        )



    # ---------------------------------------------------------
    # Mask
    # ---------------------------------------------------------

    def create_mask(
        self,
        width: int,
        height: int,
    ) -> Any:
        """
        Generate rectangle mask.

        Placeholder representation.

        Future backends:
        - Pillow
        - OpenCV
        - Qt
        - Native renderer
        """

        return {

            "type": "rectangle",

            "x": self.x,

            "y": self.y,

            "width": self.width,

            "height": self.height,

            "canvas_width": width,

            "canvas_height": height,
        }



    # ---------------------------------------------------------
    # Editing
    # ---------------------------------------------------------

    def move(
        self,
        dx: int,
        dy: int,
    ) -> None:

        if self.locked:

            return


        self.x += dx

        self.y += dy



    def resize(
        self,
        width: int,
        height: int,
    ) -> None:

        if self.locked:

            return


        self.width = max(
            1,
            width,
        )

        self.height = max(
            1,
            height,
        )



    # ---------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------

    def copy(
        self,
    ) -> "RectangleShape":

        return RectangleShape(

            self.x,

            self.y,

            self.width,

            self.height,
        )


    def __repr__(
        self,
    ) -> str:

        return (
            "RectangleShape("
            f"x={self.x}, "
            f"y={self.y}, "
            f"width={self.width}, "
            f"height={self.height}"
            ")"
        )