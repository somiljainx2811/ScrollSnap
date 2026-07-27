"""
ScrollSnap
==========

Pillow Backend

Concrete, pixel-level implementations of every abstraction that
was previously a placeholder:

    shapes.mask_renderer.MaskBackend    -> PillowMaskBackend
    stitching.blending.AlphaBlender     -> PillowAlphaBlender
    stitching.crop_optimizer.SmartCropOptimizer
                                         -> PillowCropOptimizer
    stitching.seam_optimizer.BasicSeamOptimizer
                                         -> PillowSeamOptimizer
    stitching.exporters (file writing)  -> write_export()

This is the only module in the project allowed to `import PIL`
directly for these operations - everything upstream (shapes,
stitching, preview) stays backend-agnostic and simply receives
Pillow ``Image`` objects through the ``Any`` typed parameters
already defined by those interfaces.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter

from capture.auto_scroll.scroll_detector import ScrollDetector
from image_processing.alignment import estimate_vertical_alignment
from shapes.mask_renderer import MaskBackend
from stitching.alignment import FrameAlignment
from stitching.blending import AlphaBlender
from stitching.crop_optimizer import CropBounds, SmartCropOptimizer
from stitching.duplicate_removal import DuplicateRegion, DuplicateRemover
from stitching.exporters import ExportFormat, ExportRequest
from stitching.overlap_detector import OverlapDetector, OverlapResult
from stitching.seam_optimizer import BasicSeamOptimizer
from models.frame import Frame


# ---------------------------------------------------------
# Mask Rendering
# ---------------------------------------------------------

class PillowMaskBackend(MaskBackend):
    """
    Rasterizes shape mask descriptors (produced by
    ``Shape.create_mask()``) into real alpha masks, and applies
    them to real images.
    """

    def create(
        self,
        shape: Any,
        width: int,
        height: int,
    ) -> Image.Image:

        descriptor = shape.create_mask(width, height)

        canvas_width = int(
            descriptor.get("canvas_width", width)
        )

        canvas_height = int(
            descriptor.get("canvas_height", height)
        )

        mask = Image.new(
            "L", (canvas_width, canvas_height), 0
        )

        draw = ImageDraw.Draw(mask)

        self._draw_descriptor(draw, descriptor)

        return mask

    def apply(
        self,
        image: Any,
        mask: Any,
    ) -> Image.Image:

        rgba = image.convert("RGBA")

        if mask.size != rgba.size:
            mask = mask.resize(rgba.size)

        rgba.putalpha(mask)

        bounds = mask.getbbox()

        return rgba.crop(bounds) if bounds else rgba

    # ---------------------------------------------------------
    # Descriptor Dispatch
    # ---------------------------------------------------------

    def _draw_descriptor(
        self,
        draw: ImageDraw.ImageDraw,
        descriptor: dict,
    ) -> None:

        kind = descriptor["type"]

        handler = getattr(
            self, f"_draw_{kind}", None
        )

        if handler is None:
            raise ValueError(
                f"No mask renderer for shape type '{kind}'."
            )

        handler(draw, descriptor)

    def _draw_rectangle(self, draw, descriptor: dict) -> None:

        x, y = descriptor["x"], descriptor["y"]

        draw.rectangle(
            [x, y, x + descriptor["width"], y + descriptor["height"]],
            fill=255,
        )

    def _draw_rounded_rectangle(self, draw, descriptor: dict) -> None:

        x, y = descriptor["x"], descriptor["y"]

        draw.rounded_rectangle(
            [x, y, x + descriptor["width"], y + descriptor["height"]],
            radius=descriptor["radius"],
            fill=255,
        )

    def _draw_circle(self, draw, descriptor: dict) -> None:

        x, y, r = (
            descriptor["x"],
            descriptor["y"],
            descriptor["radius"],
        )

        draw.ellipse([x, y, x + 2 * r, y + 2 * r], fill=255)

    def _draw_ellipse(self, draw, descriptor: dict) -> None:

        x, y = descriptor["x"], descriptor["y"]

        draw.ellipse(
            [x, y, x + descriptor["width"], y + descriptor["height"]],
            fill=255,
        )

    def _draw_polygon(self, draw, descriptor: dict) -> None:

        points = [tuple(p) for p in descriptor["points"]]

        if len(points) >= 2:
            draw.polygon(points, fill=255)

    def _draw_freehand(self, draw, descriptor: dict) -> None:
        self._draw_polygon(draw, descriptor)

    def _draw_star(self, draw, descriptor: dict) -> None:
        self._draw_polygon(draw, descriptor)

    def _draw_bezier(self, draw, descriptor: dict, samples: int = 20) -> None:

        points: list[tuple[float, float]] = []

        for curve in descriptor["curves"]:

            start = curve["start"]

            control1 = curve["control1"]

            control2 = curve["control2"]

            end = curve["end"]

            for index in range(samples + 1):

                t = index / samples

                inv = 1 - t

                x = (
                    inv**3 * start[0]
                    + 3 * inv**2 * t * control1[0]
                    + 3 * inv * t**2 * control2[0]
                    + t**3 * end[0]
                )

                y = (
                    inv**3 * start[1]
                    + 3 * inv**2 * t * control1[1]
                    + 3 * inv * t**2 * control2[1]
                    + t**3 * end[1]
                )

                points.append((x, y))

        if len(points) >= 2:
            draw.polygon(points, fill=255)


# ---------------------------------------------------------
# Overlap Detection (real, content-based)
# ---------------------------------------------------------

class PillowOverlapDetector(OverlapDetector):
    """
    Real, content-based replacement for
    `stitching.overlap_detector.SimpleOverlapDetector`'s flat
    "always assume 50% overlap" placeholder.

    Uses `image_processing.alignment.estimate_vertical_alignment`
    to find the actual pixel shift between two consecutive
    frames, so stitched output reflects the real scroll amount
    instead of a fixed guess.
    """

    def __init__(
        self,
        minimum_overlap: float = 0.15,
        maximum_overlap: float = 0.90,
    ) -> None:

        self.minimum_overlap = minimum_overlap

        self.maximum_overlap = maximum_overlap

    def detect(
        self,
        previous: Frame,
        current: Frame,
    ) -> OverlapResult:

        height = min(previous.height, current.height)

        width = min(previous.width, current.width)

        if (
            not isinstance(previous.image, Image.Image)
            or not isinstance(current.image, Image.Image)
        ):
            return self._fallback(height, width)

        result = estimate_vertical_alignment(
            previous.image,
            current.image,
            min_overlap_ratio=self.minimum_overlap,
            max_overlap_ratio=self.maximum_overlap,
        )

        if not result.moved:

            # No detectable scroll between these two frames
            # (duplicate/stalled capture): stack the new frame
            # directly under the previous one rather than
            # guessing, and flag it with low confidence so
            # `DuplicateRemover`/callers can act on it.
            return OverlapResult(
                found=False,
                offset_y=height,
                offset_x=0,
                overlap_height=0,
                overlap_width=width,
                confidence=0.0,
            )

        return OverlapResult(
            found=True,
            offset_y=result.shift,
            offset_x=0,
            overlap_height=result.overlap_rows,
            overlap_width=width,
            confidence=result.confidence,
        )

    def _fallback(self, height: int, width: int) -> OverlapResult:
        """
        Non-Pillow frames (shouldn't happen in this backend, but
        keeps the contract safe): fall back to the flat-50%
        heuristic rather than crashing.
        """

        estimated_overlap = int(height * 0.5)

        return OverlapResult(
            found=True,
            offset_y=height - estimated_overlap,
            offset_x=0,
            overlap_height=estimated_overlap,
            overlap_width=width,
            confidence=0.3,
        )


# ---------------------------------------------------------
# Scroll Detection (real, content-based)
# ---------------------------------------------------------

class PillowScrollDetector(ScrollDetector):
    """
    Real, content-based replacement for `ScrollDetector`'s
    hardcoded `_estimate_offset() -> 10` placeholder. Used by
    `AutoScrollEngine`/`EndDetector` to tell whether a scroll
    actually moved the page (and by how much), so "scroll until
    the page stops moving" can work for real instead of running
    until the user manually clicks Stop.
    """

    def _estimate_offset(self, previous: Any, current: Any) -> int:

        if (
            not isinstance(previous, Image.Image)
            or not isinstance(current, Image.Image)
        ):
            return 0

        result = estimate_vertical_alignment(
            previous, current, min_overlap_ratio=0.0, max_overlap_ratio=0.98,
        )

        return result.shift if result.moved else 0


# ---------------------------------------------------------
# Duplicate Frame Removal (real, content-based)
# ---------------------------------------------------------

class PillowDuplicateRemover(DuplicateRemover):
    """
    Real replacement for `DuplicateRemover`, whose `_estimate_overlap()`
    was a hardcoded "always 50%" placeholder and whose `remove()`
    never actually removed a single frame regardless of what
    `detect()` found - every frame passed straight through with
    only a metadata tag attached.

    This version genuinely detects near-identical consecutive
    frames (e.g. auto-scroll captured a few extra frames after
    the page had already stopped moving) using the same
    content-based alignment as `PillowOverlapDetector`, and
    actually drops them before stitching.
    """

    def __init__(self, minimum_match: float = 0.85) -> None:

        super().__init__(minimum_match)

        # Mean-abs-diff (0-255 scale) below which two frames are
        # considered near-identical, scaled from `minimum_match`
        # (1.0 match == 0 error, 0.0 match == max error).
        self._error_threshold = (1.0 - minimum_match) * 40.0

    def detect(self, previous: Frame, current: Frame) -> DuplicateRegion:

        if (
            not isinstance(previous.image, Image.Image)
            or not isinstance(current.image, Image.Image)
            or previous.width != current.width
            or previous.height != current.height
        ):
            return DuplicateRegion(
                found=False, height=0, start_y=0, confidence=0.0
            )

        result = estimate_vertical_alignment(
            previous.image,
            current.image,
            min_overlap_ratio=0.0,
            max_overlap_ratio=0.999,
        )

        is_duplicate = (
            not result.moved and result.error <= self._error_threshold
        )

        confidence = 1.0 - min(1.0, result.error / 40.0)

        return DuplicateRegion(
            found=is_duplicate,
            height=current.height if is_duplicate else 0,
            start_y=0,
            confidence=confidence if is_duplicate else 0.0,
        )

    def remove(self, frames: list[Frame]) -> list[Frame]:
        """
        Drop any frame that's a near-exact duplicate of the frame
        immediately before it in the (already frame-order-
        preserving) list.
        """

        if len(frames) <= 1:
            return frames

        cleaned = [frames[0]]

        for index in range(1, len(frames)):

            duplicate = self.detect(frames[index - 1], frames[index])

            if duplicate.found:
                continue  # genuinely drop it this time

            cleaned.append(frames[index])

        return cleaned


# ---------------------------------------------------------
# Blending
# ---------------------------------------------------------

class PillowAlphaBlender(AlphaBlender):
    """
    Real alpha-blended stitching backend.

    Frames are pasted top-to-bottom using their computed
    alignment. Where consecutive frames overlap, a vertical
    alpha ramp cross-fades the seam instead of a hard cut.
    """

    def merge(
        self,
        frames: list[Frame],
        alignments: list[FrameAlignment],
    ) -> Image.Image:

        canvas_width, canvas_height = self._calculate_canvas_size(
            frames, alignments
        )

        canvas = Image.new(
            "RGBA", (canvas_width, canvas_height), (0, 0, 0, 0)
        )

        placements = self._placements(frames, alignments)

        previous_bottom: int | None = None

        for frame, x, y in placements:

            image = self._as_rgba(frame.image)

            overlap = 0

            if previous_bottom is not None:
                overlap = max(0, previous_bottom - y)

            if overlap > 0:
                image = self._apply_fade_in(image, overlap)

            canvas.alpha_composite(image, (int(x), int(y)))

            previous_bottom = y + image.height

        return canvas

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _placements(
        self,
        frames: list[Frame],
        alignments: list[FrameAlignment],
    ) -> list[tuple[Frame, int, int]]:
        """
        Pair each frame with an (x, y) position. The first frame
        is placed at the origin; subsequent frames use the
        alignment computed for the *previous* frame -> this
        frame transition.
        """

        placements: list[tuple[Frame, int, int]] = [
            (frames[0], 0, 0)
        ]

        for alignment in alignments:
            placements.append(
                (
                    frames[alignment.frame_index],
                    alignment.x,
                    alignment.y,
                )
            )

        return placements

    def _as_rgba(self, image: Any) -> Image.Image:

        if not isinstance(image, Image.Image):
            raise TypeError(
                "PillowAlphaBlender requires Pillow Image frames."
            )

        return image.convert("RGBA")

    def _apply_fade_in(
        self,
        image: Image.Image,
        overlap: int,
    ) -> Image.Image:
        """
        Multiply the top `overlap` rows of `image` by a linear
        0 -> 1 alpha ramp so it cross-fades into the previous
        frame instead of overwriting it abruptly.
        """

        overlap = min(overlap, image.height)

        if overlap <= 0:
            return image

        faded = image.copy()

        alpha = faded.getchannel("A")

        ramp = Image.new("L", (faded.width, overlap))

        ramp_draw = ImageDraw.Draw(ramp)

        for row in range(overlap):

            fraction = row / max(1, overlap - 1)

            ramp_draw.line(
                [(0, row), (faded.width, row)],
                fill=int(255 * fraction),
            )

        alpha.paste(ramp, (0, 0))

        faded.putalpha(alpha)

        return faded


# ---------------------------------------------------------
# Crop Optimization
# ---------------------------------------------------------

class PillowCropOptimizer(SmartCropOptimizer):
    """
    Crops transparent/empty borders from the final stitched
    canvas using the image's own alpha channel.
    """

    def _find_bounds(self, image: Any) -> CropBounds | None:

        if not isinstance(image, Image.Image):
            return None

        rgba = image.convert("RGBA")

        bbox = rgba.getbbox()

        if bbox is None:
            return None

        left, top, right, bottom = bbox

        if self.padding:

            left = max(0, left - self.padding)

            top = max(0, top - self.padding)

            right = min(rgba.width, right + self.padding)

            bottom = min(rgba.height, bottom + self.padding)

        return CropBounds(left, top, right, bottom)

    def _crop(self, image: Any, bounds: CropBounds) -> Image.Image:

        return image.crop(
            (bounds.left, bounds.top, bounds.right, bounds.bottom)
        )


# ---------------------------------------------------------
# Seam Optimization
# ---------------------------------------------------------

class PillowSeamOptimizer(BasicSeamOptimizer):
    """
    Detects abrupt horizontal seams (rows with an unusually
    large brightness jump from the row above) and softens them
    with a small local blur.
    """

    def __init__(
        self,
        smoothing_strength: float = 0.5,
        threshold: float = 18.0,
    ) -> None:

        super().__init__(smoothing_strength)

        self.threshold = threshold

    def _detect_seams(self, image: Any) -> list[int]:

        if not isinstance(image, Image.Image):
            return []

        gray = image.convert("L")

        width, height = gray.size

        if height < 3:
            return []

        sample_width = min(width, 256)

        row_means = []

        for y in range(height):

            row = gray.crop((0, y, sample_width, y + 1))

            row_means.append(
                sum(row.getdata()) / sample_width
            )

        seams = []

        for y in range(1, height):

            if abs(row_means[y] - row_means[y - 1]) >= self.threshold:
                seams.append(y)

        return seams

    def _smooth_seams(
        self,
        image: Any,
        seams: list[int],
    ) -> Image.Image:

        result = image.copy()

        band = 3

        for seam_y in seams:

            top = max(0, seam_y - band)

            bottom = min(result.height, seam_y + band)

            if bottom <= top:
                continue

            strip = result.crop((0, top, result.width, bottom))

            blurred = strip.filter(
                ImageFilter.GaussianBlur(radius=2)
            )

            result.paste(blurred, (0, top))

        return result


# ---------------------------------------------------------
# Export (actual file writing)
# ---------------------------------------------------------

_FORMAT_EXTENSIONS = {
    ExportFormat.PNG: ".png",
    ExportFormat.JPEG: ".jpg",
    ExportFormat.WEBP: ".webp",
    ExportFormat.TIFF: ".tiff",
    ExportFormat.PDF: ".pdf",
}

_PILLOW_FORMAT_NAMES = {
    ExportFormat.PNG: "PNG",
    ExportFormat.JPEG: "JPEG",
    ExportFormat.WEBP: "WEBP",
    ExportFormat.TIFF: "TIFF",
    ExportFormat.PDF: "PDF",
}

_FLATTEN_FORMATS = {ExportFormat.JPEG, ExportFormat.PDF}


def write_export(request: ExportRequest) -> Path:
    """
    Actually write an `ExportRequest` to disk using Pillow.

    Returns the final path written (the extension is corrected
    to match the requested format if the caller's filename
    didn't already include one).
    """

    if not isinstance(request.image, Image.Image):
        raise TypeError(
            "write_export() requires a Pillow Image."
        )

    path = Path(request.filename)

    expected_ext = _FORMAT_EXTENSIONS[request.format]

    if path.suffix.lower() != expected_ext:
        path = path.with_suffix(expected_ext)

    path.parent.mkdir(parents=True, exist_ok=True)

    image = request.image

    if request.format in _FLATTEN_FORMATS and image.mode == "RGBA":

        background = Image.new("RGB", image.size, (255, 255, 255))

        background.paste(image, mask=image.getchannel("A"))

        image = background

    save_kwargs: dict[str, Any] = {}

    if request.format in (ExportFormat.JPEG, ExportFormat.WEBP):
        save_kwargs["quality"] = request.quality

    if request.format == ExportFormat.PNG:
        save_kwargs["compress_level"] = 6

    image.save(
        path,
        _PILLOW_FORMAT_NAMES[request.format],
        **save_kwargs,
    )

    return path
