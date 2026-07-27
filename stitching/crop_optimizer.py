"""
ScrollSnap
==========

Crop Optimizer

Optimizes final stitched image bounds.

Responsibilities
----------------
- Remove empty borders
- Detect content bounds
- Preserve aspect ratio
- Prepare image for export

Does NOT:
- Resize images
- Compress images
- Change quality
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from dataclasses import dataclass

from typing import Any



@dataclass(slots=True)
class CropBounds:
    """
    Represents detected content bounds.
    """

    left: int

    top: int

    right: int

    bottom: int


    @property
    def width(
        self,
    ) -> int:

        return (
            self.right -
            self.left
        )


    @property
    def height(
        self,
    ) -> int:

        return (
            self.bottom -
            self.top
        )



class CropOptimizer(ABC):
    """
    Base crop optimizer.
    """

    @abstractmethod
    def optimize(
        self,
        image: Any,
    ) -> Any:
        raise NotImplementedError



class SmartCropOptimizer(CropOptimizer):
    """
    Automatic content cropper.

    Future implementations:
    - alpha detection
    - edge detection
    - background detection
    """


    def __init__(
        self,
        padding: int = 0,
    ) -> None:

        self.padding = padding


    # ---------------------------------------------------------
    # Public
    # ---------------------------------------------------------

    def optimize(
        self,
        image: Any,
    ) -> Any:
        """
        Crop image to content.
        """

        bounds = (
            self._find_bounds(
                image
            )
        )


        if bounds is None:

            return image


        return (
            self._crop(
                image,
                bounds,
            )
        )


    # ---------------------------------------------------------
    # Detection
    # ---------------------------------------------------------

    def _find_bounds(
        self,
        image: Any,
    ) -> CropBounds | None:
        """
        Detect non-empty region.

        Placeholder.

        Future:
        - alpha scan
        - pixel variance
        - edge detection
        """

        return None


    # ---------------------------------------------------------
    # Cropping
    # ---------------------------------------------------------

    def _crop(
        self,
        image: Any,
        bounds: CropBounds,
    ) -> Any:
        """
        Apply crop operation.

        Backend specific.
        """

        return image