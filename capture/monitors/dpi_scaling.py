"""
ScrollSnap
==========

DPI Scaling Manager

Handles conversion between logical and physical coordinates.

Logical coordinates:
    Coordinates visible to applications/users.

Physical coordinates:
    Actual framebuffer pixels used for screenshots.

Example:

Windows 150% scaling:

Logical:
    100 x 100

Physical:
    150 x 150
"""

from __future__ import annotations

from dataclasses import dataclass

from models.rectangle import Rectangle


@dataclass(slots=True)
class DPIInfo:
    """
    DPI information for a display.
    """

    scale_x: float = 1.0

    scale_y: float = 1.0

    dpi_x: int = 96

    dpi_y: int = 96


class DPIScaler:
    """
    Converts between logical and physical coordinates.
    """

    BASE_DPI = 96


    def __init__(
        self,
        dpi: DPIInfo | None = None,
    ) -> None:

        self._dpi = (
            dpi
            if dpi
            else DPIInfo()
        )


    # ---------------------------------------------------------
    # Configuration
    # ---------------------------------------------------------

    @property
    def scale_x(
        self,
    ) -> float:

        return self._dpi.scale_x


    @property
    def scale_y(
        self,
    ) -> float:

        return self._dpi.scale_y


    def update(
        self,
        dpi: DPIInfo,
    ) -> None:

        self._dpi = dpi


    # ---------------------------------------------------------
    # Point Conversion
    # ---------------------------------------------------------

    def logical_to_physical(
        self,
        x: float,
        y: float,
    ) -> tuple[int, int]:

        return (
            round(
                x * self._dpi.scale_x
            ),
            round(
                y * self._dpi.scale_y
            ),
        )


    def physical_to_logical(
        self,
        x: float,
        y: float,
    ) -> tuple[int, int]:

        return (
            round(
                x / self._dpi.scale_x
            ),
            round(
                y / self._dpi.scale_y
            ),
        )


    # ---------------------------------------------------------
    # Rectangle Conversion
    # ---------------------------------------------------------

    def rectangle_to_physical(
        self,
        rect: Rectangle,
    ) -> Rectangle:

        x1, y1 = self.logical_to_physical(
            rect.x,
            rect.y,
        )

        x2, y2 = self.logical_to_physical(
            rect.x + rect.width,
            rect.y + rect.height,
        )


        return Rectangle(
            x=x1,
            y=y1,
            width=x2 - x1,
            height=y2 - y1,
        )


    def rectangle_to_logical(
        self,
        rect: Rectangle,
    ) -> Rectangle:

        x1, y1 = self.physical_to_logical(
            rect.x,
            rect.y,
        )

        x2, y2 = self.physical_to_logical(
            rect.x + rect.width,
            rect.y + rect.height,
        )


        return Rectangle(
            x=x1,
            y=y1,
            width=x2 - x1,
            height=y2 - y1,
        )


    # ---------------------------------------------------------
    # DPI Helpers
    # ---------------------------------------------------------

    @staticmethod
    def from_dpi(
        dpi_x: int,
        dpi_y: int,
    ) -> DPIInfo:

        return DPIInfo(
            scale_x=dpi_x / DPIScaler.BASE_DPI,
            scale_y=dpi_y / DPIScaler.BASE_DPI,
            dpi_x=dpi_x,
            dpi_y=dpi_y,
        )