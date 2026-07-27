"""
ScrollSnap
==========

Star Shape

Generates star-shaped capture regions.

Supports:
- Configurable points
- Inner/outer radius
- Rotation
- Polygon compatibility
"""

from __future__ import annotations

from math import (
    cos,
    sin,
    pi,
)

from typing import Any

from .polygon import (
    PolygonShape,
    Point,
)



class StarShape(PolygonShape):
    """
    Star shaped capture region.
    """


    def __init__(
        self,
        center_x: int,
        center_y: int,
        outer_radius: int,
        inner_radius: int,
        points: int = 5,
        rotation: float = -pi / 2,
    ) -> None:


        self.center_x = center_x

        self.center_y = center_y

        self.outer_radius = (
            outer_radius
        )

        self.inner_radius = (
            inner_radius
        )

        self.star_points = (
            points
        )

        self.rotation = (
            rotation
        )


        vertices = (
            self._generate_points()
        )


        super().__init__(
            vertices
        )



    # ---------------------------------------------------------
    # Generation
    # ---------------------------------------------------------

    def _generate_points(
        self,
    ) -> list[Point]:
        """
        Generate star vertices.
        """

        vertices = []


        total = (
            self.star_points *
            2
        )


        angle_step = (
            pi /
            self.star_points
        )


        for index in range(
            total
        ):

            radius = (

                self.outer_radius

                if index % 2 == 0

                else

                self.inner_radius

            )


            angle = (

                self.rotation

                +

                index *
                angle_step

            )


            x = (

                self.center_x

                +

                cos(angle)
                *
                radius

            )


            y = (

                self.center_y

                +

                sin(angle)
                *
                radius

            )


            vertices.append(

                Point(

                    int(x),

                    int(y),

                )

            )


        return vertices



    # ---------------------------------------------------------
    # Editing
    # ---------------------------------------------------------

    def regenerate(
        self,
    ) -> None:

        self.points = (
            self._generate_points()
        )



    def set_radius(
        self,
        outer: int,
        inner: int,
    ) -> None:

        if self.locked:

            return


        self.outer_radius = (
            outer
        )

        self.inner_radius = (
            inner
        )


        self.regenerate()



    # ---------------------------------------------------------
    # Mask
    # ---------------------------------------------------------

    def create_mask(
        self,
        width: int,
        height: int,
    ) -> Any:

        return {

            "type": "star",

            "points": [

                (
                    p.x,
                    p.y,
                )

                for p in self.points

            ],

            "canvas_width": width,

            "canvas_height": height,

        }



    # ---------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------

    def copy(
        self,
    ) -> "StarShape":

        return StarShape(

            self.center_x,

            self.center_y,

            self.outer_radius,

            self.inner_radius,

            self.star_points,

            self.rotation,

        )



    def __repr__(
        self,
    ) -> str:

        return (
            "StarShape("
            f"points={self.star_points}"
            ")"
        )