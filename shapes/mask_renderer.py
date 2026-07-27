"""
ScrollSnap
==========

Mask Renderer

Converts Shape objects into image masks.

Responsibilities
----------------
- Generate masks
- Apply masks to images
- Handle transparency
- Provide backend abstraction

Does NOT:
- Define shapes
- Capture screenshots
- Export files
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from dataclasses import dataclass

from typing import Any

from .base_shape import Shape



@dataclass(slots=True)
class MaskResult:
    """
    Generated mask result.
    """

    success: bool

    mask: Any | None

    width: int

    height: int

    error: str | None = None



class MaskBackend(ABC):
    """
    Backend interface.
    """


    @abstractmethod
    def create(
        self,
        shape: Shape,
        width: int,
        height: int,
    ) -> Any:
        raise NotImplementedError



    @abstractmethod
    def apply(
        self,
        image: Any,
        mask: Any,
    ) -> Any:
        raise NotImplementedError



class BasicMaskBackend(MaskBackend):
    """
    Minimal backend.

    Provides a backend-independent
    representation.

    Real rendering can later use:
    - Pillow
    - OpenCV
    - Qt
    """


    def create(
        self,
        shape: Shape,
        width: int,
        height: int,
    ) -> Any:

        return shape.create_mask(
            width,
            height,
        )



    def apply(
        self,
        image: Any,
        mask: Any,
    ) -> Any:

        return {

            "image": image,

            "mask": mask,

        }



class MaskRenderer:
    """
    High-level mask manager.
    """


    def __init__(
        self,
        backend: MaskBackend | None = None,
    ) -> None:

        self.backend = (

            backend

            or

            BasicMaskBackend()

        )



    # ---------------------------------------------------------
    # Public
    # ---------------------------------------------------------

    def render(
        self,
        shape: Shape,
        width: int,
        height: int,
    ) -> MaskResult:
        """
        Generate mask from shape.
        """

        try:

            mask = (
                self.backend.create(
                    shape,
                    width,
                    height,
                )
            )


            return MaskResult(

                success=True,

                mask=mask,

                width=width,

                height=height,

            )


        except Exception as exc:

            return MaskResult(

                success=False,

                mask=None,

                width=0,

                height=0,

                error=str(exc),

            )



    def apply(
        self,
        image: Any,
        shape: Shape,
    ) -> Any:
        """
        Apply shape mask to image.
        """

        bounds = (
            shape.bounds()
        )


        mask = (
            self.render(
                shape,
                bounds.width,
                bounds.height,
            )
        )


        if not mask.success:

            raise RuntimeError(
                mask.error
            )


        return (
            self.backend.apply(
                image,
                mask.mask,
            )
        )