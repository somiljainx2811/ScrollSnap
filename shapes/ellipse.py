"""
ScrollSnap
==========

Ellipse Shape

Provides elliptical capture regions.

Supports:
- Position
- Size
- Point containment
- Area calculation
- Mask generation
"""

from __future__ import annotations

from typing import Any

from math import pi

from .base_shape import (
    Shape,
    ShapeBounds,
)



class EllipseShape(Shape):
    """
    Elliptical capture shape.
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
        Check if point lies inside ellipse.

        Formula:

        ((x-cx)^2 / rx^2)
        +
        ((y-cy)^2 / ry^2)
        <= 1
        """

        if self.width <= 0:
            return False

        if self.height <= 0:
            return False


        cx = (
            self.x +
            self.width / 2
        )

        cy = (
            self.y +
            self.height / 2
        )


        rx = (
            self.width /
            2
        )

        ry = (
            self.height /
            2
        )


        dx = (
            x - cx
        )

        dy = (
            y - cy
        )


        value = (
            (dx * dx) /
            (rx * rx)
            +
            (dy * dy) /
            (ry * ry)
        )


        return value <= 1



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
            pi *
            (self.width / 2)
            *
            (self.height / 2)
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
        Create ellipse mask definition.
        """

        return {

            "type": "ellipse",

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
    ) -> "EllipseShape":

        return EllipseShape(

            self.x,

            self.y,

            self.width,

            self.height,
        )



    def __repr__(
        self,
    ) -> str:

        return (
            "EllipseShape("
            f"x={self.x}, "
            f"y={self.y}, "
            f"width={self.width}, "
            f"height={self.height}"
            ")"
        )