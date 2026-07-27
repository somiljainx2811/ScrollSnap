"""
ScrollSnap
==========

Circle Shape

Specialized ellipse where:
    width == height

Used for:
- Avatar captures
- Circular screenshots
- Profile images
- Round exports
"""

from __future__ import annotations

from typing import Any

from math import sqrt

from .ellipse import EllipseShape

from .base_shape import (
    ShapeBounds,
)



class CircleShape(EllipseShape):
    """
    Circular capture region.
    """


    def __init__(
        self,
        x: int,
        y: int,
        radius: int,
    ) -> None:

        diameter = (
            radius * 2
        )


        super().__init__(

            x,

            y,

            diameter,

            diameter,
        )


        self.radius = radius



    # ---------------------------------------------------------
    # Geometry
    # ---------------------------------------------------------

    def contains(
        self,
        x: int,
        y: int,
    ) -> bool:
        """
        Circle point containment.

        Formula:

        distance² <= radius²
        """

        center_x = (
            self.x +
            self.radius
        )

        center_y = (
            self.y +
            self.radius
        )


        dx = (
            x -
            center_x
        )

        dy = (
            y -
            center_y
        )


        distance = (
            dx * dx +
            dy * dy
        )


        return (
            distance <=
            self.radius *
            self.radius
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
        Create circle mask.
        """

        return {

            "type": "circle",

            "x": self.x,

            "y": self.y,

            "radius": self.radius,

            "canvas_width": width,

            "canvas_height": height,
        }



    # ---------------------------------------------------------
    # Editing
    # ---------------------------------------------------------

    def resize_radius(
        self,
        radius: int,
    ) -> None:

        if self.locked:

            return


        self.radius = max(
            1,
            radius,
        )


        diameter = (
            self.radius *
            2
        )


        self.width = diameter

        self.height = diameter



    def bounds(
        self,
    ) -> ShapeBounds:

        return ShapeBounds(

            x=self.x,

            y=self.y,

            width=self.radius * 2,

            height=self.radius * 2,
        )



    # ---------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------

    def copy(
        self,
    ) -> "CircleShape":

        return CircleShape(

            self.x,

            self.y,

            self.radius,
        )



    def __repr__(
        self,
    ) -> str:

        return (
            "CircleShape("
            f"x={self.x}, "
            f"y={self.y}, "
            f"radius={self.radius}"
            ")"
        )