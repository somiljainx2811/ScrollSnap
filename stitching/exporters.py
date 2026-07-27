"""
ScrollSnap
==========

Stitch Export Adapter

Connects the stitching pipeline with
the export subsystem.

Responsibilities
----------------
- Validate stitched output
- Prepare export metadata
- Dispatch export requests

Does NOT:
- Encode images
- Save files
- Handle compression
"""

from __future__ import annotations

from dataclasses import dataclass

from enum import Enum, auto

from typing import Any



class ExportFormat(Enum):
    """
    Supported output formats.
    """

    PNG = auto()

    JPEG = auto()

    WEBP = auto()

    TIFF = auto()

    PDF = auto()



@dataclass(slots=True)
class ExportRequest:
    """
    Export configuration.
    """

    image: Any

    format: ExportFormat

    filename: str

    quality: int = 95

    metadata: dict | None = None



@dataclass(slots=True)
class ExportResult:
    """
    Export preparation result.
    """

    success: bool

    request: ExportRequest | None

    error: str | None = None



class StitchExporter:
    """
    Converts stitched images into export requests.
    """


    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def prepare(
        self,
        image: Any,
        filename: str,
        format: ExportFormat,
        quality: int = 95,
        metadata: dict | None = None,
    ) -> ExportResult:
        """
        Prepare export operation.
        """

        try:

            self._validate(
                image
            )


            request = ExportRequest(

                image=image,

                format=format,

                filename=filename,

                quality=quality,

                metadata=metadata,
            )


            return ExportResult(

                success=True,

                request=request,
            )


        except Exception as exc:

            return ExportResult(

                success=False,

                request=None,

                error=str(exc),
            )


    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def _validate(
        self,
        image: Any,
    ) -> None:

        if image is None:

            raise ValueError(
                "Cannot export empty image."
            )