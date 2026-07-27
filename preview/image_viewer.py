"""
ScrollSnap
==========

Image Viewer

The core preview surface: combines a source image with a
ZoomController and PanController to compute what should be
visible inside a viewport, and to translate coordinates between
screen space and image space.

Responsibilities
----------------
- Hold the currently previewed image (backend agnostic)
- Combine zoom + pan into a single view transform
- Compute the visible region of the image (in image coordinates)
- Convert screen <-> image coordinates
- Provide "fit to viewport" helpers

Does NOT:
- Decode, resize, or rasterize images (left to an image backend)
- Know about widgets, canvases, or specific GUI toolkits
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.exceptions import PreviewError
from models.rectangle import Rectangle
from preview.pan import PanController
from preview.zoom import ZoomController


@dataclass(slots=True)
class ViewTransform:
    """
    A snapshot of the current view transform.
    """

    zoom: float

    pan_x: float

    pan_y: float

    viewport_width: float

    viewport_height: float


class ImageViewer:
    """
    Backend-agnostic image viewer.

    `image` may be any object exposing `.width` / `.height`
    (or a `(width, height)`-style `.size`), such as a Pillow
    Image, a Frame, or a StitchResult.
    """

    def __init__(
        self,
        zoom_controller: ZoomController | None = None,
        pan_controller: PanController | None = None,
    ) -> None:

        self._image: Any = None

        self._image_size: tuple[float, float] = (0.0, 0.0)

        self._viewport_size: tuple[float, float] = (0.0, 0.0)

        self._zoom = zoom_controller or ZoomController()

        self._pan = pan_controller or PanController()

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def zoom(self) -> ZoomController:
        return self._zoom

    @property
    def pan(self) -> PanController:
        return self._pan

    @property
    def image(self) -> Any:
        return self._image

    @property
    def has_image(self) -> bool:
        return self._image is not None

    @property
    def image_size(self) -> tuple[float, float]:
        return self._image_size

    @property
    def viewport_size(self) -> tuple[float, float]:
        return self._viewport_size

    @property
    def scaled_size(self) -> tuple[float, float]:
        """
        Size of the image after the current zoom is applied.
        """

        width, height = self._image_size

        return (
            width * self._zoom.level,
            height * self._zoom.level,
        )

    # ---------------------------------------------------------
    # Loading
    # ---------------------------------------------------------

    def load(self, image: Any) -> None:
        """
        Load a new image into the viewer, resetting zoom and pan.
        """

        self._image = image

        self._image_size = self._extract_size(image)

        self._zoom.reset()

        self._pan.reset()

    def set_image_size(
        self,
        width: float,
        height: float,
    ) -> None:
        """
        Override the tracked image size without reloading the
        underlying image object. Used after non-destructive
        edits (crop, rotate) change the effective canvas size.
        """

        if width <= 0 or height <= 0:
            raise ValueError(
                "Image dimensions must be positive."
            )

        self._image_size = (width, height)

    def set_viewport_size(
        self,
        width: float,
        height: float,
    ) -> None:
        """
        Update the known size of the viewport (the visible
        preview area, in screen pixels).
        """

        if width < 0 or height < 0:
            raise ValueError(
                "Viewport dimensions cannot be negative."
            )

        self._viewport_size = (width, height)

    # ---------------------------------------------------------
    # Fitting
    # ---------------------------------------------------------

    def fit_width(self) -> float:
        self._require_image()

        return self._zoom.fit_width(
            self._image_size[0],
            self._viewport_size[0],
        )

    def fit_height(self) -> float:
        self._require_image()

        return self._zoom.fit_height(
            self._image_size[1],
            self._viewport_size[1],
        )

    def fit_page(self) -> float:
        self._require_image()

        return self._zoom.fit_page(
            self._image_size,
            self._viewport_size,
        )

    def actual_size(self) -> float:
        """
        Reset to 100% zoom (a.k.a. "actual size").
        """

        return self._zoom.reset()

    # ---------------------------------------------------------
    # Transform
    # ---------------------------------------------------------

    def transform(self) -> ViewTransform:

        return ViewTransform(
            zoom=self._zoom.level,
            pan_x=self._pan.x,
            pan_y=self._pan.y,
            viewport_width=self._viewport_size[0],
            viewport_height=self._viewport_size[1],
        )

    def visible_region(self) -> Rectangle:
        """
        Compute the region of the *image* (in image coordinates)
        currently visible inside the viewport.
        """

        self._require_image()

        zoom = self._zoom.level

        viewport_width, viewport_height = self._viewport_size

        left = -self._pan.x / zoom

        top = -self._pan.y / zoom

        right = left + (viewport_width / zoom)

        bottom = top + (viewport_height / zoom)

        image_width, image_height = self._image_size

        region = Rectangle(left, top, right, bottom)

        bounds = Rectangle.from_xywh(
            0,
            0,
            image_width,
            image_height,
        )

        clipped = region.clip(bounds)

        return clipped if clipped is not None else Rectangle.empty()

    def clamp_pan(self, overscroll: float = 0.0) -> None:
        """
        Clamp the pan offset to keep the scaled image reachable
        within the viewport.
        """

        self._pan.clamp_to_bounds(
            self._viewport_size,
            self.scaled_size,
            overscroll=overscroll,
        )

    # ---------------------------------------------------------
    # Coordinate Conversion
    # ---------------------------------------------------------

    def screen_to_image(
        self,
        x: float,
        y: float,
    ) -> tuple[float, float]:
        """
        Convert a screen-space point into image-space coordinates.
        """

        zoom = self._zoom.level

        return (
            (x - self._pan.x) / zoom,
            (y - self._pan.y) / zoom,
        )

    def image_to_screen(
        self,
        x: float,
        y: float,
    ) -> tuple[float, float]:
        """
        Convert an image-space point into screen-space coordinates.
        """

        zoom = self._zoom.level

        return (
            (x * zoom) + self._pan.x,
            (y * zoom) + self._pan.y,
        )

    def zoom_at_point(
        self,
        screen_x: float,
        screen_y: float,
        factor: float,
    ) -> float:
        """
        Zoom in/out while keeping the point under the cursor
        stationary on screen (classic "zoom to cursor" behavior).
        """

        self._require_image()

        anchor_before = self.screen_to_image(screen_x, screen_y)

        new_level = self._zoom.set(self._zoom.level * factor)

        anchor_screen_after = (
            anchor_before[0] * new_level,
            anchor_before[1] * new_level,
        )

        self._pan.pan_to(
            screen_x - anchor_screen_after[0],
            screen_y - anchor_screen_after[1],
        )

        return new_level

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _require_image(self) -> None:

        if not self.has_image:
            raise PreviewError(
                "No image loaded into the viewer."
            )

    @staticmethod
    def _extract_size(image: Any) -> tuple[float, float]:

        if image is None:
            return (0.0, 0.0)

        width = getattr(image, "width", None)

        height = getattr(image, "height", None)

        if width is not None and height is not None:
            return (float(width), float(height))

        size = getattr(image, "size", None)

        if size is not None:
            return (float(size[0]), float(size[1]))

        raise PreviewError(
            "Unable to determine image dimensions; expected "
            "'.width'/'.height' or '.size' attributes."
        )

    def __repr__(self) -> str:

        return (
            "ImageViewer("
            f"size={self._image_size}, "
            f"zoom={self._zoom.level:.2f}, "
            f"viewport={self._viewport_size}"
            ")"
        )
