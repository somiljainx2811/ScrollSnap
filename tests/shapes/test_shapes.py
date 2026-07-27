"""
Tests for shapes/*.py: geometry, mask descriptors, copy/repr.
"""

from __future__ import annotations

from shapes.bezier import BezierCurve, BezierShape
from shapes.circle import CircleShape
from shapes.ellipse import EllipseShape
from shapes.freehand import FreehandShape
from shapes.polygon import Point, PolygonShape
from shapes.rectangle import RectangleShape
from shapes.rounded_rectangle import RoundedRectangleShape
from shapes.star import StarShape


class TestRectangleShape:

    def test_contains_inside_point(self):

        shape = RectangleShape(10, 10, 100, 50)

        assert shape.contains(50, 30)

    def test_contains_outside_point(self):

        shape = RectangleShape(10, 10, 100, 50)

        assert not shape.contains(200, 200)

    def test_create_mask_schema(self):

        shape = RectangleShape(0, 0, 50, 40)

        mask = shape.create_mask(200, 100)

        assert mask["type"] == "rectangle"

        assert mask["canvas_width"] == 200

        assert mask["canvas_height"] == 100

    def test_copy_is_independent(self):

        shape = RectangleShape(0, 0, 50, 40)

        clone = shape.copy()

        clone.x = 999

        assert shape.x == 0


class TestCircleShape:

    def test_contains_center(self):

        shape = CircleShape(0, 0, 50)

        assert shape.contains(50, 50)

    def test_mask_schema_has_radius(self):

        mask = CircleShape(10, 10, 25).create_mask(100, 100)

        assert mask["type"] == "circle"

        assert mask["radius"] == 25


class TestEllipseShape:

    def test_contains_center(self):

        shape = EllipseShape(0, 0, 100, 50)

        assert shape.contains(50, 25)

    def test_contains_far_corner_excluded(self):

        shape = EllipseShape(0, 0, 100, 50)

        assert not shape.contains(0, 0)


class TestRoundedRectangleShape:

    def test_mask_schema_has_radius(self):

        mask = RoundedRectangleShape(0, 0, 80, 60, 12).create_mask(100, 100)

        assert mask["type"] == "rounded_rectangle"

        assert mask["radius"] == 12


class TestPolygonShape:

    def test_mask_contains_points(self):

        points = [Point(0, 0), Point(50, 0), Point(25, 50)]

        shape = PolygonShape(points)

        mask = shape.create_mask(100, 100)

        assert mask["type"] == "polygon"

        assert len(mask["points"]) == 3


class TestFreehandShape:

    def test_mask_schema(self):

        points = [Point(0, 0), Point(10, 10), Point(20, 0)]

        mask = FreehandShape(points).create_mask(50, 50)

        assert mask["type"] == "freehand"


class TestStarShape:

    def test_generates_ten_vertices_for_five_points(self):

        star = StarShape(
            center_x=50, center_y=50,
            outer_radius=40, inner_radius=15, points=5,
        )

        assert len(star.points) == 10

    def test_copy_preserves_geometry(self):

        star = StarShape(50, 50, 40, 15, points=6)

        clone = star.copy()

        assert clone.star_points == 6

        assert clone.outer_radius == 40


class TestBezierShape:

    def test_samples_produce_points(self):

        curve = BezierCurve(
            Point(0, 0), Point(10, -20), Point(40, -20), Point(50, 0)
        )

        shape = BezierShape([curve], samples=10)

        assert len(shape.points) == 11  # samples + 1

    def test_mask_schema_has_curves(self):

        curve = BezierCurve(
            Point(0, 0), Point(10, -20), Point(40, -20), Point(50, 0)
        )

        mask = BezierShape([curve]).create_mask(100, 100)

        assert mask["type"] == "bezier"

        assert len(mask["curves"]) == 1
