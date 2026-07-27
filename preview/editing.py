"""
ScrollSnap
==========

Editing Session

Tracks non-destructive image edits made in the preview: crop,
rotate, flip, and basic adjustments. Edits are recorded as an
ordered list of operations rather than being applied to pixels
directly, so the same session can be undone, redone, replayed,
or handed to any rendering backend.

Responsibilities
----------------
- Record crop / rotate / flip / adjustment operations
- Maintain undo / redo history
- Compute the resulting (pre-render) canvas size after edits
- Produce a backend-agnostic "edit plan" for a renderer to apply

Does NOT:
- Decode or manipulate actual pixels
- Know about any specific imaging library
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from core.exceptions import PreviewError
from models.rectangle import Rectangle


MAX_HISTORY = 100


class EditKind(Enum):
    """
    Supported non-destructive edit operations.
    """

    CROP = auto()

    ROTATE = auto()

    FLIP_HORIZONTAL = auto()

    FLIP_VERTICAL = auto()

    BRIGHTNESS = auto()

    CONTRAST = auto()

    SATURATION = auto()


@dataclass(slots=True)
class EditOperation:
    """
    A single recorded edit operation.

    `value` meaning depends on `kind`:
        CROP               -> Rectangle (in current canvas coords)
        ROTATE             -> degrees, clockwise (float)
        FLIP_HORIZONTAL /
        FLIP_VERTICAL      -> None
        BRIGHTNESS /
        CONTRAST /
        SATURATION         -> float multiplier, 1.0 = unchanged
    """

    kind: EditKind

    value: Any = None

    def to_dict(self) -> dict[str, object]:

        value = self.value

        if isinstance(value, Rectangle):
            value = value.to_dict()

        return {
            "kind": self.kind.name,
            "value": value,
        }


class EditingSession:
    """
    Records and replays non-destructive edits applied to a
    single preview image.
    """

    def __init__(
        self,
        original_size: tuple[float, float],
    ) -> None:

        if original_size[0] <= 0 or original_size[1] <= 0:
            raise ValueError(
                "original_size must be positive."
            )

        self._original_size = original_size

        self._operations: list[EditOperation] = []

        self._undo_stack: list[list[EditOperation]] = []

        self._redo_stack: list[list[EditOperation]] = []

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def original_size(self) -> tuple[float, float]:
        return self._original_size

    @property
    def operations(self) -> list[EditOperation]:
        return list(self._operations)

    @property
    def has_edits(self) -> bool:
        return bool(self._operations)

    @property
    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    # ---------------------------------------------------------
    # Crop
    # ---------------------------------------------------------

    def crop(self, region: Rectangle) -> None:
        """
        Record a crop to `region`, expressed in the coordinate
        space of the canvas as it exists *after* prior edits.
        """

        canvas = self.current_size()

        bounds = Rectangle.from_xywh(
            0,
            0,
            canvas[0],
            canvas[1],
        )

        clipped = region.clip(bounds)

        if clipped is None or clipped.is_empty:
            raise PreviewError(
                "Crop region does not intersect the image."
            )

        self._record(EditOperation(EditKind.CROP, clipped))

    # ---------------------------------------------------------
    # Rotate / Flip
    # ---------------------------------------------------------

    def rotate(self, degrees: float) -> None:
        """
        Record a clockwise rotation, in degrees. Normalized to
        the [0, 360) range.
        """

        normalized = degrees % 360

        self._record(
            EditOperation(EditKind.ROTATE, normalized)
        )

    def rotate_90_cw(self) -> None:
        self.rotate(90)

    def rotate_90_ccw(self) -> None:
        self.rotate(-90)

    def flip_horizontal(self) -> None:
        self._record(
            EditOperation(EditKind.FLIP_HORIZONTAL, None)
        )

    def flip_vertical(self) -> None:
        self._record(
            EditOperation(EditKind.FLIP_VERTICAL, None)
        )

    # ---------------------------------------------------------
    # Adjustments
    # ---------------------------------------------------------

    def set_brightness(self, multiplier: float) -> None:
        self._replace_or_add(
            EditKind.BRIGHTNESS,
            self._validate_multiplier(multiplier),
        )

    def set_contrast(self, multiplier: float) -> None:
        self._replace_or_add(
            EditKind.CONTRAST,
            self._validate_multiplier(multiplier),
        )

    def set_saturation(self, multiplier: float) -> None:
        self._replace_or_add(
            EditKind.SATURATION,
            self._validate_multiplier(multiplier),
        )

    @staticmethod
    def _validate_multiplier(value: float) -> float:

        if value < 0:
            raise ValueError(
                "Adjustment multiplier cannot be negative."
            )

        return value

    def _replace_or_add(
        self,
        kind: EditKind,
        value: float,
    ) -> None:
        """
        Adjustments are continuous (dragged via a slider), so
        repeated calls update the most recent operation of the
        same kind rather than growing the history unbounded.
        """

        if (
            self._operations
            and self._operations[-1].kind == kind
        ):

            self._snapshot()

            self._operations[-1] = EditOperation(kind, value)

        else:

            self._record(EditOperation(kind, value))

    # ---------------------------------------------------------
    # Canvas Size
    # ---------------------------------------------------------

    def current_size(self) -> tuple[float, float]:
        """
        Compute the canvas size after every recorded operation.
        """

        width, height = self._original_size

        for operation in self._operations:

            if operation.kind == EditKind.CROP:

                region: Rectangle = operation.value

                width, height = region.width, region.height

            elif operation.kind == EditKind.ROTATE:

                if operation.value in (90.0, 270.0):
                    width, height = height, width

        return (width, height)

    # ---------------------------------------------------------
    # Undo / Redo
    # ---------------------------------------------------------

    def undo(self) -> bool:

        if not self._undo_stack:
            return False

        self._redo_stack.append(list(self._operations))

        self._operations = self._undo_stack.pop()

        return True

    def redo(self) -> bool:

        if not self._redo_stack:
            return False

        self._undo_stack.append(list(self._operations))

        self._operations = self._redo_stack.pop()

        return True

    def reset(self) -> None:
        """
        Discard every edit, returning to the original image.
        """

        if self._operations:
            self._snapshot()

        self._operations.clear()

    # ---------------------------------------------------------
    # Plan Export
    # ---------------------------------------------------------

    def plan(self) -> list[dict[str, object]]:
        """
        Produce a backend-agnostic, ordered list of operations
        an image processing backend can apply sequentially.
        """

        return [op.to_dict() for op in self._operations]

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _record(self, operation: EditOperation) -> None:

        self._snapshot()

        self._operations.append(operation)

    def _snapshot(self) -> None:

        self._undo_stack.append(list(self._operations))

        if len(self._undo_stack) > MAX_HISTORY:
            self._undo_stack.pop(0)

        self._redo_stack.clear()

    def __repr__(self) -> str:

        return (
            "EditingSession("
            f"operations={len(self._operations)}, "
            f"size={self.current_size()}"
            ")"
        )
