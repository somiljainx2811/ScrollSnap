"""
ScrollSnap
==========

Base Shape System

Defines the interface for all capture shapes.

Every shape must support:

- Geometry definition
- Point containment
- Bounding box calculation
- Mask generation preparation

Examples:

Rectangle
Circle
Polygon
Freehand
Bezier
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from dataclasses import dataclass

from typing import Any



@dataclass(slots=True)
class ShapeBounds:
    """
    Bounding rectangle of a shape.
    """

    x: int

    y: int

    width: int

    height: int



class Shape(ABC):
    """
    Abstract capture shape.
    """


    def __init__(
        self,
    ) -> None:

        self._locked = False



    # ---------------------------------------------------------
    # Geometry
    # ---------------------------------------------------------

    @abstractmethod
    def contains(
        self,
        x: int,
        y: int,
    ) -> bool:
        """
        Check whether a point belongs
        inside the shape.
        """
        raise NotImplementedError



    @abstractmethod
    def bounds(
        self,
    ) -> ShapeBounds:
        """
        Return bounding rectangle.
        """
        raise NotImplementedError



    @abstractmethod
    def area(
        self,
    ) -> float:
        """
        Return shape area.
        """
        raise NotImplementedError



    # ---------------------------------------------------------
    # Mask
    # ---------------------------------------------------------

    @abstractmethod
    def create_mask(
        self,
        width: int,
        height: int,
    ) -> Any:
        """
        Create a binary/alpha mask.

        White:
            Keep content

        Black:
            Remove content
        """
        raise NotImplementedError



    # ---------------------------------------------------------
    # State
    # ---------------------------------------------------------

    def lock(
        self,
    ) -> None:

        self._locked = True



    def unlock(
        self,
    ) -> None:

        self._locked = False



    @property
    def locked(
        self,
    ) -> bool:

        return self._locked



    # ---------------------------------------------------------
    # Transformation hooks
    # ---------------------------------------------------------

    def move(
        self,
        dx: int,
        dy: int,
    ) -> None:
        """
        Move shape.

        Implemented by shapes that support
        editing.
        """

        raise NotImplementedError



    def resize(
        self,
        width: int,
        height: int,
    ) -> None:
        """
        Resize shape.
        """

        raise NotImplementedError