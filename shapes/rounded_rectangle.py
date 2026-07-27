"""
ScrollSnap
==========

Rounded Rectangle Shape

Extends rectangle selection with rounded corners.

Supports:
- Rectangle geometry
- Corner radius
- Point containment
- Rounded mask generation
"""

from __future__ import annotations

from typing import Any

from .rectangle import RectangleShape

from .base_shape import (
    ShapeBounds,
)



class RoundedRectangleShape(RectangleShape):
    """
    Rounded rectangle capture region.
    """


    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        radius: int = 20,
    ) -> None:

        super().__init__(
            x,
            y,
            width,
            height,
        )


        self.radius = max(
            0,
            radius,
        )



    # ---------------------------------------------------------
    # Geometry
    # ---------------------------------------------------------

    def contains(
        self,
        x: int,
        y: int,
    ) -> bool:
        """
        Checks whether point exists
        inside rounded rectangle.

        Uses corner circle tests.
        """

        if not super().contains(
            x,
            y,
        ):
            return False


        radius = self.radius


        # Inside rectangle center area

        if (
            self.x + radius <= x <=
            self.x + self.width - radius
        ):

            return True


        if (
            self.y + radius <= y <=
            self.y + self.height - radius
        ):

            return True



        # Corner circle checks

        corners = [

            (
                self.x + radius,
                self.y + radius,
            ),

            (
                self.x + self.width - radius,
                self.y + radius,
            ),

            (
                self.x + radius,
                self.y + self.height - radius,
            ),

            (
                self.x + self.width - radius,
                self.y + self.height - radius,
            ),
        ]


        for cx, cy in corners:

            dx = x - cx

            dy = y - cy


            if (
                dx * dx +
                dy * dy
                <=
                radius * radius
            ):
                return True


        return False



    # ---------------------------------------------------------
    # Mask
    # ---------------------------------------------------------

    def create_mask(
        self,
        width: int,
        height: int,
    ) -> Any:
        """
        Generate rounded rectangle mask.
        """

        return {

            "type": "rounded_rectangle",

            "x": self.x,

            "y": self.y,

            "width": self.width,

            "height": self.height,

            "radius": self.radius,

            "canvas_width": width,

            "canvas_height": height,
        }



    # ---------------------------------------------------------
    # Editing
    # ---------------------------------------------------------

    def set_radius(
        self,
        radius: int,
    ) -> None:

        if self.locked:

            return


        max_radius = min(
            self.width,
            self.height,
        ) // 2


        self.radius = min(
            max(
                0,
                radius,
            ),
            max_radius,
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



    # ---------------------------------------------------------
    # Copy
    # ---------------------------------------------------------

    def copy(
        self,
    ) -> "RoundedRectangleShape":

        return RoundedRectangleShape(

            self.x,

            self.y,

            self.width,

            self.height,

            self.radius,
        )



    def __repr__(
        self,
    ) -> str:

        return (
            "RoundedRectangleShape("
            f"x={self.x}, "
            f"y={self.y}, "
            f"width={self.width}, "
            f"height={self.height}, "
            f"radius={self.radius}"
            ")"
        )