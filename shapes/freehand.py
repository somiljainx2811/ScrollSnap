"""
ScrollSnap
==========

Freehand Shape

Mouse-drawn custom capture region.

Supports:
- Free drawing
- Path recording
- Point containment
- Smoothing hooks
- Mask generation
"""

from __future__ import annotations

from dataclasses import dataclass

from typing import Any

from .polygon import (
    PolygonShape,
    Point,
)

from .base_shape import (
    ShapeBounds,
)



@dataclass(slots=True)
class FreehandConfig:
    """
    Freehand configuration.
    """

    smoothing: float = 0.5

    minimum_points: int = 3



class FreehandShape(PolygonShape):
    """
    Freehand/lasso capture shape.
    """


    def __init__(
        self,
        points: list[Point] | None = None,
        config: FreehandConfig | None = None,
    ) -> None:


        self.config = (
            config
            or
            FreehandConfig()
        )


        super().__init__(

            points
            or []

        )



    # ---------------------------------------------------------
    # Drawing
    # ---------------------------------------------------------

    def add_point(
        self,
        x: int,
        y: int,
    ) -> None:
        """
        Add mouse movement point.
        """

        if self.locked:

            return


        self.points.append(

            Point(
                x,
                y,
            )

        )



    def finish(
        self,
    ) -> None:
        """
        Close freehand path.

        Connect last point to first.
        """

        if len(
            self.points
        ) < self.config.minimum_points:

            raise ValueError(
                "Not enough points."
            )


        if (
            self.points[0].x
            !=
            self.points[-1].x

            or

            self.points[0].y
            !=
            self.points[-1].y
        ):

            self.points.append(

                Point(

                    self.points[0].x,

                    self.points[0].y,

                )

            )



    # ---------------------------------------------------------
    # Optimization
    # ---------------------------------------------------------

    def smooth(
        self,
    ) -> None:
        """
        Reduce unnecessary points.

        Placeholder.

        Future:
        - Douglas-Peucker
        - Bezier fitting
        - spline smoothing
        """

        if len(
            self.points
        ) <= 4:

            return


        simplified = [

            self.points[0]

        ]


        for index in range(
            1,
            len(self.points)-1,
        ):

            previous = (
                self.points[index-1]
            )

            current = (
                self.points[index]
            )


            distance = (

                abs(
                    current.x -
                    previous.x
                )

                +

                abs(
                    current.y -
                    previous.y
                )

            )


            if distance > 3:

                simplified.append(
                    current
                )


        simplified.append(
            self.points[-1]
        )


        self.points = simplified



    # ---------------------------------------------------------
    # Mask
    # ---------------------------------------------------------

    def create_mask(
        self,
        width: int,
        height: int,
    ) -> Any:

        return {

            "type": "freehand",

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
    ) -> "FreehandShape":

        return FreehandShape(

            [

                Point(
                    p.x,
                    p.y,
                )

                for p in self.points

            ],

            self.config,

        )



    def __repr__(
        self,
    ) -> str:

        return (
            "FreehandShape("
            f"points={len(self.points)}"
            ")"
        )