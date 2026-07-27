"""
ScrollSnap
==========

Annotations

Data model and layer management for markup drawn on top of a
preview image: arrows, shapes, text, highlights, blur regions,
freehand ink, and numbered step stamps.

Responsibilities
----------------
- Define annotation data (backend agnostic)
- Manage an ordered collection of annotations ("layer")
- Support selection, z-ordering, and hit testing
- Provide undo / redo history for annotation edits

Does NOT:
- Rasterize or draw annotations onto pixels
  (left to an image processing backend, mirroring
  shapes/mask_renderer.py's MaskBackend abstraction)
- Handle mouse/keyboard input directly
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any
from uuid import uuid4

from models.rectangle import Rectangle


class AnnotationType(Enum):
    """
    Supported annotation kinds.
    """

    ARROW = auto()

    LINE = auto()

    RECTANGLE = auto()

    ELLIPSE = auto()

    HIGHLIGHT = auto()

    BLUR = auto()

    PIXELATE = auto()

    TEXT = auto()

    FREEHAND = auto()

    STEP_NUMBER = auto()


DEFAULT_COLOR = "#FF3B30"

DEFAULT_STROKE_WIDTH = 3.0

MAX_HISTORY = 100


@dataclass(slots=True)
class Annotation:
    """
    A single piece of markup.

    `points` holds shape-specific geometry:
        ARROW / LINE          -> [start, end]
        RECTANGLE / ELLIPSE   -> [top_left, bottom_right]
        HIGHLIGHT / BLUR /
        PIXELATE              -> [top_left, bottom_right]
        FREEHAND              -> [p0, p1, ..., pn]
        TEXT / STEP_NUMBER     -> [anchor]
    """

    type: AnnotationType

    points: list[tuple[float, float]] = field(default_factory=list)

    id: str = field(default_factory=lambda: str(uuid4()))

    color: str = DEFAULT_COLOR

    stroke_width: float = DEFAULT_STROKE_WIDTH

    fill: bool = False

    opacity: float = 1.0

    text: str = ""

    font_size: float = 18.0

    z_index: int = 0

    locked: bool = False

    visible: bool = True

    metadata: dict[str, object] = field(default_factory=dict)

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def __post_init__(self) -> None:

        if not (0.0 <= self.opacity <= 1.0):
            raise ValueError(
                "opacity must be between 0.0 and 1.0."
            )

        if self.stroke_width < 0:
            raise ValueError(
                "stroke_width cannot be negative."
            )

    # ---------------------------------------------------------
    # Geometry
    # ---------------------------------------------------------

    def bounds(self) -> Rectangle:
        """
        Axis-aligned bounding box of this annotation, padded
        by the stroke width so hit testing / redraw regions
        include the full visible stroke.
        """

        if not self.points:
            return Rectangle.empty()

        xs = [p[0] for p in self.points]

        ys = [p[1] for p in self.points]

        pad = max(self.stroke_width, self.font_size * 0.5)

        return Rectangle(
            min(xs) - pad,
            min(ys) - pad,
            max(xs) + pad,
            max(ys) + pad,
        )

    def translate(self, dx: float, dy: float) -> None:
        """
        Move every point by (dx, dy) in place.
        """

        self.points = [
            (x + dx, y + dy) for (x, y) in self.points
        ]

    # ---------------------------------------------------------
    # Serialization
    # ---------------------------------------------------------

    def to_dict(self) -> dict[str, object]:

        return {
            "id": self.id,
            "type": self.type.name,
            "points": [list(p) for p in self.points],
            "color": self.color,
            "stroke_width": self.stroke_width,
            "fill": self.fill,
            "opacity": self.opacity,
            "text": self.text,
            "font_size": self.font_size,
            "z_index": self.z_index,
            "locked": self.locked,
            "visible": self.visible,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Annotation":

        return cls(
            type=AnnotationType[str(data["type"])],
            points=[
                (float(p[0]), float(p[1]))
                for p in data.get("points", [])  # type: ignore[union-attr]
            ],
            id=str(data.get("id", uuid4())),
            color=str(data.get("color", DEFAULT_COLOR)),
            stroke_width=float(
                data.get("stroke_width", DEFAULT_STROKE_WIDTH)
            ),
            fill=bool(data.get("fill", False)),
            opacity=float(data.get("opacity", 1.0)),
            text=str(data.get("text", "")),
            font_size=float(data.get("font_size", 18.0)),
            z_index=int(data.get("z_index", 0)),
            locked=bool(data.get("locked", False)),
            visible=bool(data.get("visible", True)),
            metadata=dict(data.get("metadata", {})),  # type: ignore[arg-type]
        )

    def copy(self) -> "Annotation":
        return deepcopy(self)

    def __repr__(self) -> str:

        return (
            "Annotation("
            f"type={self.type.name}, "
            f"id={self.id[:8]}, "
            f"points={len(self.points)}"
            ")"
        )


class AnnotationLayer:
    """
    Ordered collection of annotations with selection,
    z-ordering, and undo / redo support.
    """

    def __init__(self) -> None:

        self._annotations: list[Annotation] = []

        self._selected_id: str | None = None

        self._undo_stack: list[list[Annotation]] = []

        self._redo_stack: list[list[Annotation]] = []

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def annotations(self) -> list[Annotation]:
        return list(self._annotations)

    @property
    def count(self) -> int:
        return len(self._annotations)

    @property
    def is_empty(self) -> bool:
        return not self._annotations

    @property
    def selected(self) -> Annotation | None:
        return self.find(self._selected_id)

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    # ---------------------------------------------------------
    # Mutation
    # ---------------------------------------------------------

    def add(self, annotation: Annotation) -> Annotation:
        """
        Add a new annotation, recording undo history.
        """

        self._snapshot()

        annotation.z_index = len(self._annotations)

        self._annotations.append(annotation)

        self._selected_id = annotation.id

        return annotation

    def remove(self, annotation_id: str) -> bool:
        """
        Remove an annotation by id.
        """

        annotation = self.find(annotation_id)

        if annotation is None:
            return False

        self._snapshot()

        self._annotations.remove(annotation)

        if self._selected_id == annotation_id:
            self._selected_id = None

        return True

    def update(
        self,
        annotation_id: str,
        **changes: object,
    ) -> Annotation | None:
        """
        Apply field updates to an existing annotation.
        """

        annotation = self.find(annotation_id)

        if annotation is None:
            return None

        self._snapshot()

        for key, value in changes.items():

            if not hasattr(annotation, key):
                raise AttributeError(
                    f"Annotation has no field '{key}'."
                )

            setattr(annotation, key, value)

        return annotation

    def clear(self) -> None:
        """
        Remove every annotation.
        """

        if self._annotations:
            self._snapshot()

        self._annotations.clear()

        self._selected_id = None

    # ---------------------------------------------------------
    # Selection
    # ---------------------------------------------------------

    def select(self, annotation_id: str | None) -> None:
        self._selected_id = annotation_id

    def find(self, annotation_id: str | None) -> Annotation | None:

        if annotation_id is None:
            return None

        for annotation in self._annotations:
            if annotation.id == annotation_id:
                return annotation

        return None

    def hit_test(self, x: float, y: float) -> Annotation | None:
        """
        Return the topmost visible, unlocked annotation whose
        bounds contain the given point.
        """

        for annotation in sorted(
            self._annotations,
            key=lambda a: a.z_index,
            reverse=True,
        ):

            if not annotation.visible or annotation.locked:
                continue

            if annotation.bounds().contains_point((x, y)):
                return annotation

        return None

    # ---------------------------------------------------------
    # Z-Ordering
    # ---------------------------------------------------------

    def bring_to_front(self, annotation_id: str) -> None:

        annotation = self.find(annotation_id)

        if annotation is None:
            return

        self._snapshot()

        max_z = max(
            (a.z_index for a in self._annotations),
            default=0,
        )

        annotation.z_index = max_z + 1

    def send_to_back(self, annotation_id: str) -> None:

        annotation = self.find(annotation_id)

        if annotation is None:
            return

        self._snapshot()

        min_z = min(
            (a.z_index for a in self._annotations),
            default=0,
        )

        annotation.z_index = min_z - 1

    # ---------------------------------------------------------
    # Undo / Redo
    # ---------------------------------------------------------

    def undo(self) -> bool:

        if not self._undo_stack:
            return False

        self._redo_stack.append(
            [a.copy() for a in self._annotations]
        )

        self._annotations = self._undo_stack.pop()

        self._selected_id = None

        return True

    def redo(self) -> bool:

        if not self._redo_stack:
            return False

        self._undo_stack.append(
            [a.copy() for a in self._annotations]
        )

        self._annotations = self._redo_stack.pop()

        self._selected_id = None

        return True

    # ---------------------------------------------------------
    # Serialization
    # ---------------------------------------------------------

    def to_list(self) -> list[dict[str, object]]:
        return [a.to_dict() for a in self._annotations]

    @classmethod
    def from_list(
        cls,
        data: list[dict[str, object]],
    ) -> "AnnotationLayer":

        layer = cls()

        layer._annotations = [
            Annotation.from_dict(item) for item in data
        ]

        return layer

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _snapshot(self) -> None:

        self._undo_stack.append(
            [a.copy() for a in self._annotations]
        )

        if len(self._undo_stack) > MAX_HISTORY:
            self._undo_stack.pop(0)

        self._redo_stack.clear()

    def __repr__(self) -> str:

        return (
            "AnnotationLayer("
            f"count={len(self._annotations)}, "
            f"selected={self._selected_id}"
            ")"
        )
