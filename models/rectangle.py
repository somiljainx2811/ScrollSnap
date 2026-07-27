"""
ScrollSnap
==========

Rectangle Geometry

A production-grade immutable rectangle implementation used throughout
ScrollSnap.

This class is intentionally independent from Qt/OpenCV/Pillow so it can
be reused by every subsystem.

Used by:
    - Capture Region
    - Selection Overlay
    - Auto Scroll
    - Preview
    - Image Stitching
    - Cropping
    - OCR
    - Export
    - Plugins

Coordinate System
-----------------

left <= right
top  <= bottom

Coordinates may be negative.

The rectangle follows the inclusive-exclusive convention:

    left <= x < right
    top  <= y < bottom

This matches most graphics APIs.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Iterator


Number = int | float


@dataclass(frozen=True, slots=True)
class Rectangle:
    """
    Immutable rectangle.

    Parameters
    ----------
    left
        Left coordinate.

    top
        Top coordinate.

    right
        Right coordinate.

    bottom
        Bottom coordinate.
    """

    left: Number
    top: Number
    right: Number
    bottom: Number

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def __post_init__(self) -> None:
        if not all(
            isinstance(v, (int, float))
            for v in (
                self.left,
                self.top,
                self.right,
                self.bottom,
            )
        ):
            raise TypeError(
                "Rectangle coordinates must be numeric."
            )

    # ---------------------------------------------------------
    # Constructors
    # ---------------------------------------------------------

    @classmethod
    def from_xywh(
        cls,
        x: Number,
        y: Number,
        width: Number,
        height: Number,
    ) -> "Rectangle":
        """
        Construct from x, y, width, height.
        """

        return cls(
            x,
            y,
            x + width,
            y + height,
        )

    @classmethod
    def from_points(
        cls,
        p1: tuple[Number, Number],
        p2: tuple[Number, Number],
    ) -> "Rectangle":
        """
        Construct from two corner points.
        """

        x1, y1 = p1
        x2, y2 = p2

        return cls(
            min(x1, x2),
            min(y1, y2),
            max(x1, x2),
            max(y1, y2),
        )

    @classmethod
    def from_center(
        cls,
        center_x: Number,
        center_y: Number,
        width: Number,
        height: Number,
    ) -> "Rectangle":
        """
        Construct from center point.
        """

        hw = width / 2
        hh = height / 2

        return cls(
            center_x - hw,
            center_y - hh,
            center_x + hw,
            center_y + hh,
        )

    @classmethod
    def empty(cls) -> "Rectangle":
        """
        Returns an empty rectangle.
        """

        return cls(
            0,
            0,
            0,
            0,
        )

    # ---------------------------------------------------------
    # Basic Properties
    # ---------------------------------------------------------

    @property
    def width(self) -> Number:
        return self.right - self.left

    @property
    def height(self) -> Number:
        return self.bottom - self.top

    @property
    def area(self) -> Number:
        return self.width * self.height

    @property
    def perimeter(self) -> Number:
        return 2 * (self.width + self.height)

    @property
    def center(self) -> tuple[float, float]:
        return (
            (self.left + self.right) / 2,
            (self.top + self.bottom) / 2,
        )

    @property
    def size(self) -> tuple[Number, Number]:
        return (
            self.width,
            self.height,
        )

    @property
    def top_left(self) -> tuple[Number, Number]:
        return (
            self.left,
            self.top,
        )

    @property
    def top_right(self) -> tuple[Number, Number]:
        return (
            self.right,
            self.top,
        )

    @property
    def bottom_left(self) -> tuple[Number, Number]:
        return (
            self.left,
            self.bottom,
        )

    @property
    def bottom_right(self) -> tuple[Number, Number]:
        return (
            self.right,
            self.bottom,
        )

    @property
    def aspect_ratio(self) -> float:
        """
        Width divided by height.

        Returns
        -------
        float

        Raises
        ------
        ZeroDivisionError
            If height is zero.
        """

        return self.width / self.height

    @property
    def diagonal(self) -> float:
        """
        Length of diagonal.
        """

        return sqrt(
            self.width ** 2 +
            self.height ** 2
        )

    @property
    def is_empty(self) -> bool:
        """
        True if width or height is zero.
        """

        return (
            self.width == 0
            or self.height == 0
        )

    @property
    def is_valid(self) -> bool:
        """
        Returns True if rectangle dimensions are non-negative.
        """

        return (
            self.width >= 0
            and self.height >= 0
        )

    @property
    def normalized(self) -> "Rectangle":
        """
        Returns a normalized rectangle.

        Guarantees

            left <= right
            top <= bottom
        """

        return Rectangle(
            min(self.left, self.right),
            min(self.top, self.bottom),
            max(self.left, self.right),
            max(self.top, self.bottom),
        )

    # ---------------------------------------------------------
    # Geometry
    # ---------------------------------------------------------

    def contains(
        self,
        x: Number,
        y: Number,
    ) -> bool:
        """
        Returns True if point lies inside rectangle.
        """

        return (
            self.left <= x < self.right
            and
            self.top <= y < self.bottom
        )

    def contains_point(
        self,
        point: tuple[Number, Number],
    ) -> bool:
        """
        Returns True if point lies inside rectangle.
        """

        return self.contains(
            point[0],
            point[1],
        )

    def contains_rectangle(
        self,
        other: "Rectangle",
    ) -> bool:
        """
        Returns True if other rectangle is fully contained.
        """

        return (
            self.left <= other.left
            and
            self.top <= other.top
            and
            self.right >= other.right
            and
            self.bottom >= other.bottom
        )

        # ---------------------------------------------------------
    # Rectangle Relationships
    # ---------------------------------------------------------

    def intersects(
        self,
        other: "Rectangle",
    ) -> bool:
        """
        Returns True if two rectangles overlap with positive area.
        """

        return not (
            self.right <= other.left
            or self.left >= other.right
            or self.bottom <= other.top
            or self.top >= other.bottom
        )

    def touches(
        self,
        other: "Rectangle",
    ) -> bool:
        """
        Returns True if rectangles touch or overlap.
        """

        return not (
            self.right < other.left
            or self.left > other.right
            or self.bottom < other.top
            or self.top > other.bottom
        )

    def intersection(
        self,
        other: "Rectangle",
    ) -> "Rectangle":
        """
        Returns the overlapping rectangle.

        If there is no overlap, returns Rectangle.empty().
        """

        if not self.intersects(other):
            return Rectangle.empty()

        return Rectangle(
            max(self.left, other.left),
            max(self.top, other.top),
            min(self.right, other.right),
            min(self.bottom, other.bottom),
        )

    def union(
        self,
        other: "Rectangle",
    ) -> "Rectangle":
        """
        Smallest rectangle containing both rectangles.
        """

        return Rectangle(
            min(self.left, other.left),
            min(self.top, other.top),
            max(self.right, other.right),
            max(self.bottom, other.bottom),
        )

    def overlap_area(
        self,
        other: "Rectangle",
    ) -> Number:
        """
        Area of the overlapping region.
        """

        return self.intersection(other).area

    def intersection_over_union(
        self,
        other: "Rectangle",
    ) -> float:
        """
        Computes the Intersection over Union (IoU).

        Widely used in image processing and object detection.
        """

        intersection = self.overlap_area(other)

        union = self.area + other.area - intersection

        if union == 0:
            return 0.0

        return intersection / union

    # ---------------------------------------------------------
    # Transformations
    # ---------------------------------------------------------

    def translate(
        self,
        dx: Number,
        dy: Number,
    ) -> "Rectangle":
        """
        Move rectangle by the given offset.
        """

        return Rectangle(
            self.left + dx,
            self.top + dy,
            self.right + dx,
            self.bottom + dy,
        )

    def move_to(
        self,
        x: Number,
        y: Number,
    ) -> "Rectangle":
        """
        Move rectangle so its top-left corner is at (x, y).
        """

        return Rectangle.from_xywh(
            x,
            y,
            self.width,
            self.height,
        )

    def inflate(
        self,
        dx: Number,
        dy: Number,
    ) -> "Rectangle":
        """
        Grow rectangle equally in all directions.
        """

        return Rectangle(
            self.left - dx,
            self.top - dy,
            self.right + dx,
            self.bottom + dy,
        )

    def deflate(
        self,
        dx: Number,
        dy: Number,
    ) -> "Rectangle":
        """
        Shrink rectangle equally in all directions.
        """

        return Rectangle(
            self.left + dx,
            self.top + dy,
            self.right - dx,
            self.bottom - dy,
        )

    def scale(
        self,
        sx: Number,
        sy: Number | None = None,
    ) -> "Rectangle":
        """
        Scale rectangle around its center.
        """

        if sy is None:
            sy = sx

        cx, cy = self.center

        half_width = (self.width * sx) / 2
        half_height = (self.height * sy) / 2

        return Rectangle(
            cx - half_width,
            cy - half_height,
            cx + half_width,
            cy + half_height,
        )

    # ---------------------------------------------------------
    # Clipping
    # ---------------------------------------------------------

    def clip(
        self,
        bounds: "Rectangle",
    ) -> "Rectangle":
        """
        Clip this rectangle to another rectangle.

        Equivalent to intersection().
        """

        return self.intersection(bounds)

    def clamp(
        self,
        bounds: "Rectangle",
    ) -> "Rectangle":
        """
        Move the rectangle so it fits entirely inside bounds
        while preserving its size.
        """

        width = self.width
        height = self.height

        x = min(
            max(self.left, bounds.left),
            bounds.right - width,
        )

        y = min(
            max(self.top, bounds.top),
            bounds.bottom - height,
        )

        return Rectangle.from_xywh(
            x,
            y,
            width,
            height,
        )

    # ---------------------------------------------------------
    # Distance
    # ---------------------------------------------------------

    def distance_to(
        self,
        other: "Rectangle",
    ) -> float:
        """
        Minimum Euclidean distance between two rectangles.

        Returns 0 if they intersect.
        """

        if self.intersects(other):
            return 0.0

        dx = max(
            other.left - self.right,
            self.left - other.right,
            0,
        )

        dy = max(
            other.top - self.bottom,
            self.top - other.bottom,
            0,
        )

        return sqrt(dx * dx + dy * dy)

    # ---------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------

    def expand_to_include(
        self,
        x: Number,
        y: Number,
    ) -> "Rectangle":
        """
        Returns a rectangle expanded to include the given point.
        """

        return Rectangle(
            min(self.left, x),
            min(self.top, y),
            max(self.right, x),
            max(self.bottom, y),
        )

    def snap(
        self,
        grid_size: Number,
    ) -> "Rectangle":
        """
        Snap rectangle coordinates to a grid.
        """

        if grid_size <= 0:
            raise ValueError("grid_size must be positive.")

        return Rectangle(
            round(self.left / grid_size) * grid_size,
            round(self.top / grid_size) * grid_size,
            round(self.right / grid_size) * grid_size,
            round(self.bottom / grid_size) * grid_size,
        )

        # ---------------------------------------------------------
    # Rectangle Relationships
    # ---------------------------------------------------------

    def intersects(
        self,
        other: "Rectangle",
    ) -> bool:
        """
        Returns True if two rectangles overlap with positive area.
        """

        return not (
            self.right <= other.left
            or self.left >= other.right
            or self.bottom <= other.top
            or self.top >= other.bottom
        )

    def touches(
        self,
        other: "Rectangle",
    ) -> bool:
        """
        Returns True if rectangles touch or overlap.
        """

        return not (
            self.right < other.left
            or self.left > other.right
            or self.bottom < other.top
            or self.top > other.bottom
        )

    def intersection(
        self,
        other: "Rectangle",
    ) -> "Rectangle":
        """
        Returns the overlapping rectangle.

        If there is no overlap, returns Rectangle.empty().
        """

        if not self.intersects(other):
            return Rectangle.empty()

        return Rectangle(
            max(self.left, other.left),
            max(self.top, other.top),
            min(self.right, other.right),
            min(self.bottom, other.bottom),
        )

    def union(
        self,
        other: "Rectangle",
    ) -> "Rectangle":
        """
        Smallest rectangle containing both rectangles.
        """

        return Rectangle(
            min(self.left, other.left),
            min(self.top, other.top),
            max(self.right, other.right),
            max(self.bottom, other.bottom),
        )

    def overlap_area(
        self,
        other: "Rectangle",
    ) -> Number:
        """
        Area of the overlapping region.
        """

        return self.intersection(other).area

    def intersection_over_union(
        self,
        other: "Rectangle",
    ) -> float:
        """
        Computes the Intersection over Union (IoU).

        Widely used in image processing and object detection.
        """

        intersection = self.overlap_area(other)

        union = self.area + other.area - intersection

        if union == 0:
            return 0.0

        return intersection / union

    # ---------------------------------------------------------
    # Transformations
    # ---------------------------------------------------------

    def translate(
        self,
        dx: Number,
        dy: Number,
    ) -> "Rectangle":
        """
        Move rectangle by the given offset.
        """

        return Rectangle(
            self.left + dx,
            self.top + dy,
            self.right + dx,
            self.bottom + dy,
        )

    def move_to(
        self,
        x: Number,
        y: Number,
    ) -> "Rectangle":
        """
        Move rectangle so its top-left corner is at (x, y).
        """

        return Rectangle.from_xywh(
            x,
            y,
            self.width,
            self.height,
        )

    def inflate(
        self,
        dx: Number,
        dy: Number,
    ) -> "Rectangle":
        """
        Grow rectangle equally in all directions.
        """

        return Rectangle(
            self.left - dx,
            self.top - dy,
            self.right + dx,
            self.bottom + dy,
        )

    def deflate(
        self,
        dx: Number,
        dy: Number,
    ) -> "Rectangle":
        """
        Shrink rectangle equally in all directions.
        """

        return Rectangle(
            self.left + dx,
            self.top + dy,
            self.right - dx,
            self.bottom - dy,
        )

    def scale(
        self,
        sx: Number,
        sy: Number | None = None,
    ) -> "Rectangle":
        """
        Scale rectangle around its center.
        """

        if sy is None:
            sy = sx

        cx, cy = self.center

        half_width = (self.width * sx) / 2
        half_height = (self.height * sy) / 2

        return Rectangle(
            cx - half_width,
            cy - half_height,
            cx + half_width,
            cy + half_height,
        )

    # ---------------------------------------------------------
    # Clipping
    # ---------------------------------------------------------

    def clip(
        self,
        bounds: "Rectangle",
    ) -> "Rectangle":
        """
        Clip this rectangle to another rectangle.

        Equivalent to intersection().
        """

        return self.intersection(bounds)

    def clamp(
        self,
        bounds: "Rectangle",
    ) -> "Rectangle":
        """
        Move the rectangle so it fits entirely inside bounds
        while preserving its size.
        """

        width = self.width
        height = self.height

        x = min(
            max(self.left, bounds.left),
            bounds.right - width,
        )

        y = min(
            max(self.top, bounds.top),
            bounds.bottom - height,
        )

        return Rectangle.from_xywh(
            x,
            y,
            width,
            height,
        )

    # ---------------------------------------------------------
    # Distance
    # ---------------------------------------------------------

    def distance_to(
        self,
        other: "Rectangle",
    ) -> float:
        """
        Minimum Euclidean distance between two rectangles.

        Returns 0 if they intersect.
        """

        if self.intersects(other):
            return 0.0

        dx = max(
            other.left - self.right,
            self.left - other.right,
            0,
        )

        dy = max(
            other.top - self.bottom,
            self.top - other.bottom,
            0,
        )

        return sqrt(dx * dx + dy * dy)

    # ---------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------

    def expand_to_include(
        self,
        x: Number,
        y: Number,
    ) -> "Rectangle":
        """
        Returns a rectangle expanded to include the given point.
        """

        return Rectangle(
            min(self.left, x),
            min(self.top, y),
            max(self.right, x),
            max(self.bottom, y),
        )

    def snap(
        self,
        grid_size: Number,
    ) -> "Rectangle":
        """
        Snap rectangle coordinates to a grid.
        """

        if grid_size <= 0:
            raise ValueError("grid_size must be positive.")

        return Rectangle(
            round(self.left / grid_size) * grid_size,
            round(self.top / grid_size) * grid_size,
            round(self.right / grid_size) * grid_size,
            round(self.bottom / grid_size) * grid_size,
        )

    # ---------------------------------------------------------
    # Serialization
    # ---------------------------------------------------------

    def to_dict(self) -> dict[str, Number]:
        """
        Serialize this rectangle to a plain dict.
        """

        return {
            "left": self.left,
            "top": self.top,
            "right": self.right,
            "bottom": self.bottom,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Number]) -> "Rectangle":
        """
        Reconstruct a rectangle from a dict produced by
        `to_dict()`.
        """

        return cls(
            data["left"],
            data["top"],
            data["right"],
            data["bottom"],
        )
