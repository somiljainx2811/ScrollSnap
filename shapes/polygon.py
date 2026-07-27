"""
ScrollSnap
==========

Polygon Shape

Custom multi-point capture region.

Supports:
- Arbitrary vertices
- Point containment
- Bounding calculation
- Mask generation
"""

from __future__ import annotations

from typing import Any

from dataclasses import dataclass

from .base_shape import (
    Shape,
    ShapeBounds,
)



@dataclass(slots=True)
class Point:
    """
    Polygon point.
    """

    x: int

    y: int



class PolygonShape(Shape):
    """
    Custom polygon capture shape.
    """


    def __init__(
        self,
        points: list[Point],
    ) -> None:

        super().__init__()


        if len(points) < 3:

            raise ValueError(
                "Polygon requires at least 3 points."
            )


        self.points = points



    # ---------------------------------------------------------
    # Geometry
    # ---------------------------------------------------------

    def contains(
        self,
        x: int,
        y: int,
    ) -> bool:
        """
        Ray casting algorithm.

        Determines whether a point
        lies inside polygon.
        """

        inside = False


        count = len(
            self.points
        )


        j = count - 1


        for i in range(count):

            xi = (
                self.points[i].x
            )

            yi = (
                self.points[i].y
            )


            xj = (
                self.points[j].x
            )

            yj = (
                self.points[j].y
            )


            intersect = (

                (
                    yi > y
                )
                !=
                (
                    yj > y
                )

                and

                (
                    x <
                    (
                        xj - xi
                    )
                    *
                    (
                        y - yi
                    )
                    /
                    (
                        yj - yi
                    )
                    +
                    xi
                )
            )


            if intersect:

                inside = not inside


            j = i


        return inside



    def bounds(
        self,
    ) -> ShapeBounds:

        xs = [
            p.x
            for p in self.points
        ]

        ys = [
            p.y
            for p in self.points
        ]


        left = min(xs)

        top = min(ys)

        right = max(xs)

        bottom = max(ys)


        return ShapeBounds(

            x=left,

            y=top,

            width=right-left,

            height=bottom-top,
        )



    def area(
        self,
    ) -> float:
        """
        Shoelace formula.
        """

        area = 0

        n = len(
            self.points
        )


        for i in range(n):

            j = (
                i + 1
            ) % n


            area += (

                self.points[i].x
                *
                self.points[j].y

            )

            area -= (

                self.points[j].x
                *
                self.points[i].y

            )


        return abs(
            area
        ) / 2



    # ---------------------------------------------------------
    # Mask
    # ---------------------------------------------------------

    def create_mask(
        self,
        width: int,
        height: int,
    ) -> Any:
        """
        Polygon mask definition.
        """

        return {

            "type": "polygon",

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
    # Editing
    # ---------------------------------------------------------

    def move(
        self,
        dx: int,
        dy: int,
    ) -> None:

        if self.locked:

            return


        for point in self.points:

            point.x += dx

            point.y += dy



    def add_point(
        self,
        point: Point,
    ) -> None:

        if self.locked:

            return


        self.points.append(
            point
        )



    def remove_point(
        self,
        index: int,
    ) -> None:

        if self.locked:

            return


        if (
            0 <= index <
            len(self.points)
        ):

            self.points.pop(
                index
            )



    # ---------------------------------------------------------
    # Utility
    # ---------------------------------------------------------

    def copy(
        self,
    ) -> "PolygonShape":

        return PolygonShape(

            [

                Point(
                    p.x,
                    p.y,
                )

                for p in self.points

            ]

        )



    def __repr__(
        self,
    ) -> str:

        return (
            "PolygonShape("
            f"points={len(self.points)}"
            ")"
        )