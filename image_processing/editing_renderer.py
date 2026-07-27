"""
ScrollSnap
==========

Editing Renderer

Applies a `preview.editing.EditingSession` plan (crop / rotate /
flip / adjustments) and a `preview.annotations.AnnotationLayer`
export (arrows, shapes, text, blur, etc.) onto a real Pillow
image.

This is the rendering backend for `preview.preview_window`'s
`PreviewPlan`: everything upstream describes *what* to do in
backend-agnostic dicts; this module is what actually does it.
"""

from __future__ import annotations

from typing import Any

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from core.exceptions import PreviewError


DEFAULT_FONT_SIZE = 18.0


# ---------------------------------------------------------
# Edit Operations
# ---------------------------------------------------------

def apply_edits(
    image: Image.Image,
    plan: list[dict[str, object]],
) -> Image.Image:
    """
    Apply an ordered list of edit operations (as produced by
    `EditingSession.plan()`) to `image`, returning a new image.
    """

    result = image

    for operation in plan:

        kind = operation["kind"]

        value = operation.get("value")

        handler = _EDIT_HANDLERS.get(kind)

        if handler is None:
            raise PreviewError(
                f"No renderer for edit operation '{kind}'."
            )

        result = handler(result, value)

    return result


def _apply_crop(image: Image.Image, value: dict) -> Image.Image:

    return image.crop(
        (
            int(value["left"]),
            int(value["top"]),
            int(value["right"]),
            int(value["bottom"]),
        )
    )


def _apply_rotate(image: Image.Image, value: float) -> Image.Image:

    # PIL rotates counter-clockwise for positive angles;
    # our EditingSession records clockwise degrees.
    return image.rotate(-float(value), expand=True)


def _apply_flip_horizontal(image: Image.Image, _value: Any) -> Image.Image:

    return image.transpose(Image.FLIP_LEFT_RIGHT)


def _apply_flip_vertical(image: Image.Image, _value: Any) -> Image.Image:

    return image.transpose(Image.FLIP_TOP_BOTTOM)


def _apply_brightness(image: Image.Image, value: float) -> Image.Image:

    return ImageEnhance.Brightness(image).enhance(float(value))


def _apply_contrast(image: Image.Image, value: float) -> Image.Image:

    return ImageEnhance.Contrast(image).enhance(float(value))


def _apply_saturation(image: Image.Image, value: float) -> Image.Image:

    return ImageEnhance.Color(image).enhance(float(value))


_EDIT_HANDLERS = {
    "CROP": _apply_crop,
    "ROTATE": _apply_rotate,
    "FLIP_HORIZONTAL": _apply_flip_horizontal,
    "FLIP_VERTICAL": _apply_flip_vertical,
    "BRIGHTNESS": _apply_brightness,
    "CONTRAST": _apply_contrast,
    "SATURATION": _apply_saturation,
}


# ---------------------------------------------------------
# Annotations
# ---------------------------------------------------------

def render_annotations(
    image: Image.Image,
    annotations: list[dict[str, object]],
) -> Image.Image:
    """
    Burn every visible annotation (as produced by
    `AnnotationLayer.to_list()`) into `image`, returning a new
    RGBA image.
    """

    result = image.convert("RGBA")

    ordered = sorted(
        annotations, key=lambda a: a.get("z_index", 0)
    )

    for annotation in ordered:

        if not annotation.get("visible", True):
            continue

        kind = annotation["type"]

        handler = _ANNOTATION_HANDLERS.get(kind)

        if handler is None:
            raise PreviewError(
                f"No renderer for annotation type '{kind}'."
            )

        result = handler(result, annotation)

    return result


def _color_with_opacity(color: str, opacity: float) -> tuple:

    color = color.lstrip("#")

    r = int(color[0:2], 16)

    g = int(color[2:4], 16)

    b = int(color[4:6], 16)

    return (r, g, b, int(255 * opacity))


def _points_of(annotation: dict) -> list[tuple[float, float]]:

    return [tuple(p) for p in annotation["points"]]


def _draw_arrow(image: Image.Image, annotation: dict) -> Image.Image:

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))

    draw = ImageDraw.Draw(overlay)

    start, end = _points_of(annotation)

    color = _color_with_opacity(
        annotation["color"], annotation["opacity"]
    )

    width = max(1, int(annotation["stroke_width"]))

    draw.line([start, end], fill=color, width=width)

    _draw_arrowhead(draw, start, end, color, width)

    image.alpha_composite(overlay)

    return image


def _draw_arrowhead(
    draw: ImageDraw.ImageDraw,
    start: tuple[float, float],
    end: tuple[float, float],
    color: tuple,
    width: int,
) -> None:

    from math import atan2, cos, sin, pi

    angle = atan2(end[1] - start[1], end[0] - start[0])

    length = max(10.0, width * 4)

    spread = pi / 7

    left = (
        end[0] - length * cos(angle - spread),
        end[1] - length * sin(angle - spread),
    )

    right = (
        end[0] - length * cos(angle + spread),
        end[1] - length * sin(angle + spread),
    )

    draw.polygon([end, left, right], fill=color)


def _draw_line(image: Image.Image, annotation: dict) -> Image.Image:

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))

    draw = ImageDraw.Draw(overlay)

    color = _color_with_opacity(
        annotation["color"], annotation["opacity"]
    )

    draw.line(
        _points_of(annotation),
        fill=color,
        width=max(1, int(annotation["stroke_width"])),
    )

    image.alpha_composite(overlay)

    return image


def _draw_freehand(image: Image.Image, annotation: dict) -> Image.Image:

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))

    draw = ImageDraw.Draw(overlay)

    color = _color_with_opacity(
        annotation["color"], annotation["opacity"]
    )

    points = _points_of(annotation)

    width = max(1, int(annotation["stroke_width"]))

    if len(points) >= 2:

        draw.line(
            points, fill=color, width=width, joint="curve"
        )

    image.alpha_composite(overlay)

    return image


def _rect_bounds(annotation: dict) -> tuple[float, float, float, float]:

    (x1, y1), (x2, y2) = _points_of(annotation)

    return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))


def _draw_rectangle(image: Image.Image, annotation: dict) -> Image.Image:

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))

    draw = ImageDraw.Draw(overlay)

    color = _color_with_opacity(
        annotation["color"], annotation["opacity"]
    )

    bounds = _rect_bounds(annotation)

    draw.rectangle(
        bounds,
        outline=color,
        fill=color if annotation["fill"] else None,
        width=max(1, int(annotation["stroke_width"])),
    )

    image.alpha_composite(overlay)

    return image


def _draw_ellipse(image: Image.Image, annotation: dict) -> Image.Image:

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))

    draw = ImageDraw.Draw(overlay)

    color = _color_with_opacity(
        annotation["color"], annotation["opacity"]
    )

    bounds = _rect_bounds(annotation)

    draw.ellipse(
        bounds,
        outline=color,
        fill=color if annotation["fill"] else None,
        width=max(1, int(annotation["stroke_width"])),
    )

    image.alpha_composite(overlay)

    return image


def _draw_highlight(image: Image.Image, annotation: dict) -> Image.Image:

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))

    draw = ImageDraw.Draw(overlay)

    color = _color_with_opacity(
        annotation["color"], annotation["opacity"] * 0.4
    )

    draw.rectangle(_rect_bounds(annotation), fill=color)

    image.alpha_composite(overlay)

    return image


def _draw_blur(image: Image.Image, annotation: dict) -> Image.Image:

    bounds = tuple(int(v) for v in _rect_bounds(annotation))

    region = image.crop(bounds)

    blurred = region.filter(ImageFilter.GaussianBlur(radius=12))

    image.paste(blurred, bounds[:2])

    return image


def _draw_pixelate(image: Image.Image, annotation: dict) -> Image.Image:

    bounds = tuple(int(v) for v in _rect_bounds(annotation))

    left, top, right, bottom = bounds

    width = max(1, right - left)

    height = max(1, bottom - top)

    region = image.crop(bounds)

    block = max(4, min(width, height) // 12)

    small = region.resize(
        (max(1, width // block), max(1, height // block)),
        Image.NEAREST,
    )

    pixelated = small.resize((width, height), Image.NEAREST)

    image.paste(pixelated, (left, top))

    return image


_FONT_CANDIDATES = (
    "DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "Arial Bold.ttf",
    "arialbd.ttf",
    "Arial.ttf",
    "arial.ttf",
)


def _load_font(size: float) -> ImageFont.FreeTypeFont:

    for candidate in _FONT_CANDIDATES:

        try:
            return ImageFont.truetype(candidate, int(size))

        except OSError:
            continue

    return ImageFont.load_default()


def _draw_text(image: Image.Image, annotation: dict) -> Image.Image:

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))

    draw = ImageDraw.Draw(overlay)

    color = _color_with_opacity(
        annotation["color"], annotation["opacity"]
    )

    anchor = tuple(annotation["points"][0])

    font = _load_font(
        annotation.get("font_size", DEFAULT_FONT_SIZE)
    )

    draw.text(anchor, annotation.get("text", ""), fill=color, font=font)

    image.alpha_composite(overlay)

    return image


def _draw_step_number(image: Image.Image, annotation: dict) -> Image.Image:

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))

    draw = ImageDraw.Draw(overlay)

    color = _color_with_opacity(
        annotation["color"], annotation["opacity"]
    )

    x, y = tuple(annotation["points"][0])

    radius = max(10.0, annotation.get("font_size", DEFAULT_FONT_SIZE))

    draw.ellipse(
        [x - radius, y - radius, x + radius, y + radius], fill=color
    )

    font = _load_font(radius)

    text = str(annotation.get("text", ""))

    bbox = draw.textbbox((0, 0), text, font=font)

    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    draw.text(
        (x - text_w / 2, y - text_h / 2),
        text,
        fill=(255, 255, 255, 255),
        font=font,
    )

    image.alpha_composite(overlay)

    return image


_ANNOTATION_HANDLERS = {
    "ARROW": _draw_arrow,
    "LINE": _draw_line,
    "RECTANGLE": _draw_rectangle,
    "ELLIPSE": _draw_ellipse,
    "HIGHLIGHT": _draw_highlight,
    "BLUR": _draw_blur,
    "PIXELATE": _draw_pixelate,
    "TEXT": _draw_text,
    "FREEHAND": _draw_freehand,
    "STEP_NUMBER": _draw_step_number,
}


# ---------------------------------------------------------
# Full Plan Rendering
# ---------------------------------------------------------

def render_plan(
    source: Image.Image,
    edits: list[dict[str, object]],
    annotations: list[dict[str, object]],
) -> Image.Image:
    """
    Apply edits, then burn in annotations, producing the final
    exportable image for a `preview.preview_window.PreviewPlan`.
    """

    edited = apply_edits(source, edits)

    return render_annotations(edited, annotations)
