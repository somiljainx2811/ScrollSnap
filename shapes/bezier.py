"""
ScrollSnap
==========

Bezier Shape

Vector based curved capture region.

Supports:
- Cubic Bezier curves
- Control points
- Curve sampling
- Polygon conversion
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
class BezierCurve:
    """
    Cubic Bezier curve segment.
    """

    start: Point

    control1: Point

    control2: Point

    end: Point



class BezierShape(PolygonShape):
    """
    Bezier based capture shape.

    Internally converted into polygon
    for compatibility.
    """


    def __init__(
        self,
        curves: list[BezierCurve],
        samples: int = 20,
    ) -> None:

        self.curves = curves

        self.samples = max(
            4,
            samples,
        )


        points = (
            self._sample_curves()
        )


        super().__init__(
            points
        )



    # ---------------------------------------------------------
    # Curve Sampling
    # ---------------------------------------------------------

    def _sample_curves(
        self,
    ) -> list[Point]:
        """
        Convert curves into points.
        """

        result = []


        for curve in self.curves:

            for index in range(
                self.samples + 1
            ):

                t = (
                    index /
                    self.samples
                )


                point = (
                    self._calculate_point(
                        curve,
                        t,
                    )
                )


                result.append(
                    point
                )


        return result



    def _calculate_point(
        self,
        curve: BezierCurve,
        t: float,
    ) -> Point:
        """
        Cubic Bezier equation.
        """

        inverse = (
            1 - t
        )


        x = (

            inverse ** 3
            *
            curve.start.x

            +

            3 *
            inverse ** 2 *
            t *
            curve.control1.x

            +

            3 *
            inverse *
            t ** 2 *
            curve.control2.x

            +

            t ** 3 *
            curve.end.x

        )


        y = (

            inverse ** 3
            *
            curve.start.y

            +

            3 *
            inverse ** 2 *
            t *
            curve.control1.y

            +

            3 *
            inverse *
            t ** 2 *
            curve.control2.y

            +

            t ** 3 *
            curve.end.y

        )


        return Point(

            int(x),

            int(y),

        )



    # ---------------------------------------------------------
    # Editing
    # ---------------------------------------------------------

    def regenerate(
        self,
    ) -> None:
        """
        Rebuild polygon approximation
        after curve edits.
        """

        self.points = (
            self._sample_curves()
        )



    # ---------------------------------------------------------
    # Mask
    # ---------------------------------------------------------

    def create_mask(
        self,
        width: int,
        height: int,
    ) -> Any:

        return {

            "type": "bezier",

            "curves": [

                {

                    "start":
                        (
                            c.start.x,
                            c.start.y,
                        ),

                    "control1":
                        (
                            c.control1.x,
                            c.control1.y,
                        ),

                    "control2":
                        (
                            c.control2.x,
                            c.control2.y,
                        ),

                    "end":
                        (
                            c.end.x,
                            c.end.y,
                        ),

                }

                for c in self.curves

            ],

            "canvas_width": width,

            "canvas_height": height,
        }



    # ---------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------

    def copy(
        self,
    ) -> "BezierShape":

        curves = [

            BezierCurve(

                Point(
                    c.start.x,
                    c.start.y,
                ),

                Point(
                    c.control1.x,
                    c.control1.y,
                ),

                Point(
                    c.control2.x,
                    c.control2.y,
                ),

                Point(
                    c.end.x,
                    c.end.y,
                ),

            )

            for c in self.curves

        ]


        return BezierShape(

            curves,

            self.samples,

        )



    def __repr__(
        self,
    ) -> str:

        return (
            "BezierShape("
            f"curves={len(self.curves)}"
            ")"
        )