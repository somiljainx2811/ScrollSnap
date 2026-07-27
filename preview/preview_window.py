"""
ScrollSnap
==========

Preview Window

The high-level coordinator for the "preview before save" workflow.

This ties together:

    ImageViewer        - zoom / pan / coordinate conversion
    EditingSession      - crop / rotate / flip / adjustments
    AnnotationLayer     - arrows, text, highlights, blur, etc.
    ComparisonView      - before / after comparison
    NavigationController - browsing multiple frames or history

and drives an explicit state machine so the UI layer never has
to juggle scattered boolean flags.

Workflow
--------
Stitch Engine
      |
      v
PreviewWindow.open(image)
      |
      v
  VIEWING <--> EDITING <--> ANNOTATING
      |
      v
  COMPARING (optional)
      |
      v
  EXPORTING
      |
      v
  CLOSED

Does NOT:
- Render pixels
- Write files
- Know about any specific GUI toolkit
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from core.event_bus import EventBus, event_bus as default_event_bus
from core.exceptions import PreviewError
from models.rectangle import Rectangle
from preview.annotations import AnnotationLayer
from preview.comparison import ComparisonMode, ComparisonView
from preview.editing import EditingSession
from preview.image_viewer import ImageViewer
from preview.navigation import NavigationController


class PreviewState(Enum):
    """
    Explicit preview lifecycle states.
    """

    IDLE = auto()

    VIEWING = auto()

    EDITING = auto()

    ANNOTATING = auto()

    COMPARING = auto()

    EXPORTING = auto()

    CLOSED = auto()


# States from which each transition is legal.
_ALLOWED_TRANSITIONS: dict[PreviewState, set[PreviewState]] = {
    PreviewState.IDLE: {PreviewState.VIEWING},
    PreviewState.VIEWING: {
        PreviewState.EDITING,
        PreviewState.ANNOTATING,
        PreviewState.COMPARING,
        PreviewState.EXPORTING,
        PreviewState.CLOSED,
    },
    PreviewState.EDITING: {
        PreviewState.VIEWING,
        PreviewState.ANNOTATING,
        PreviewState.CLOSED,
    },
    PreviewState.ANNOTATING: {
        PreviewState.VIEWING,
        PreviewState.EDITING,
        PreviewState.CLOSED,
    },
    PreviewState.COMPARING: {
        PreviewState.VIEWING,
        PreviewState.CLOSED,
    },
    PreviewState.EXPORTING: {
        PreviewState.VIEWING,
        PreviewState.CLOSED,
    },
    PreviewState.CLOSED: set(),
}


@dataclass(slots=True)
class PreviewPlan:
    """
    Everything an export/render backend needs to produce the
    final image: the source, the edit operations, and the
    annotations to burn in.
    """

    source: Any

    edits: list[dict[str, object]]

    annotations: list[dict[str, object]]

    output_size: tuple[float, float]


class PreviewWindow:
    """
    Coordinates the full "preview before save" workflow for a
    single image (or a navigable sequence of images).
    """

    def __init__(
        self,
        images: list[Any] | None = None,
        bus: EventBus | None = None,
    ) -> None:

        self._state = PreviewState.IDLE

        self._images: list[Any] = list(images or [])

        self._bus = bus or default_event_bus

        self._viewer = ImageViewer()

        self._editing: EditingSession | None = None

        self._annotations = AnnotationLayer()

        self._comparison = ComparisonView()

        self._navigation = NavigationController(
            count=len(self._images)
        )

        self._navigation.subscribe(self._on_navigate)

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def state(self) -> PreviewState:
        return self._state

    @property
    def viewer(self) -> ImageViewer:
        return self._viewer

    @property
    def editing(self) -> EditingSession:

        if self._editing is None:
            raise PreviewError(
                "No image is currently loaded."
            )

        return self._editing

    @property
    def annotations(self) -> AnnotationLayer:
        return self._annotations

    @property
    def comparison(self) -> ComparisonView:
        return self._comparison

    @property
    def navigation(self) -> NavigationController:
        return self._navigation

    @property
    def is_open(self) -> bool:
        return self._state not in (
            PreviewState.IDLE,
            PreviewState.CLOSED,
        )

    @property
    def is_dirty(self) -> bool:
        """
        Whether the current image has unsaved edits or markup.
        """

        has_edits = (
            self._editing is not None
            and self._editing.has_edits
        )

        return has_edits or not self._annotations.is_empty

    @property
    def can_undo(self) -> bool:

        if self._state == PreviewState.ANNOTATING:
            return self._annotations.can_undo

        if self._editing is not None:
            return self._editing.can_undo

        return False

    @property
    def can_redo(self) -> bool:

        if self._state == PreviewState.ANNOTATING:
            return self._annotations.can_redo

        if self._editing is not None:
            return self._editing.can_redo

        return False

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def open(
        self,
        images: list[Any] | Any,
    ) -> None:
        """
        Open one image, or a navigable list of images, for
        preview.
        """

        self._images = (
            images if isinstance(images, list) else [images]
        )

        if not self._images:
            raise PreviewError(
                "Cannot open a preview with no images."
            )

        self._navigation.set_count(len(self._images))

        self._navigation.go_to(0)

        self._load_current()

        self._transition(PreviewState.VIEWING)

        self._publish("preview.opened")

    def close(self) -> None:
        """
        Close the preview, discarding in-memory viewer state.
        """

        if self._state == PreviewState.CLOSED:
            return

        self._transition(PreviewState.CLOSED)

        self._publish("preview.closed")

    # ---------------------------------------------------------
    # Modes
    # ---------------------------------------------------------

    def enter_editing(self) -> None:
        self._transition(PreviewState.EDITING)
        self._publish("preview.editing.entered")

    def enter_annotating(self) -> None:
        self._transition(PreviewState.ANNOTATING)
        self._publish("preview.annotating.entered")

    def enter_comparing(
        self,
        mode: ComparisonMode = ComparisonMode.SLIDER,
    ) -> None:

        if self._editing is None:
            raise PreviewError(
                "No image is currently loaded."
            )

        self._comparison.set_images(
            self._images[self._navigation.index],
            self._viewer.image,
        )

        self._comparison.set_mode(mode)

        self._transition(PreviewState.COMPARING)

        self._publish("preview.comparing.entered")

    def return_to_viewing(self) -> None:
        self._transition(PreviewState.VIEWING)
        self._publish("preview.viewing.entered")

    # ---------------------------------------------------------
    # Navigation
    # ---------------------------------------------------------

    def next_image(self) -> None:
        self._navigation.next()

    def previous_image(self) -> None:
        self._navigation.previous()

    def go_to_image(self, index: int) -> None:
        self._navigation.go_to(index)

    # ---------------------------------------------------------
    # Editing Shortcuts
    # ---------------------------------------------------------

    def crop(self, region: Rectangle) -> None:

        self.editing.crop(region)

        self._refit_after_edit()

        self._publish("preview.edited", {"kind": "crop"})

    def rotate(self, degrees: float) -> None:

        self.editing.rotate(degrees)

        self._refit_after_edit()

        self._publish("preview.edited", {"kind": "rotate"})

    def flip_horizontal(self) -> None:

        self.editing.flip_horizontal()

        self._publish(
            "preview.edited", {"kind": "flip_horizontal"}
        )

    def flip_vertical(self) -> None:

        self.editing.flip_vertical()

        self._publish(
            "preview.edited", {"kind": "flip_vertical"}
        )

    # ---------------------------------------------------------
    # Undo / Redo
    # ---------------------------------------------------------

    def undo(self) -> bool:

        if self._state == PreviewState.ANNOTATING:
            result = self._annotations.undo()

        elif self._editing is not None:
            result = self._editing.undo()

        else:
            result = False

        if result:
            self._publish("preview.undo")

        return result

    def redo(self) -> bool:

        if self._state == PreviewState.ANNOTATING:
            result = self._annotations.redo()

        elif self._editing is not None:
            result = self._editing.redo()

        else:
            result = False

        if result:
            self._publish("preview.redo")

        return result

    # ---------------------------------------------------------
    # Export
    # ---------------------------------------------------------

    def build_plan(self) -> PreviewPlan:
        """
        Produce a backend-agnostic plan describing exactly how
        to render the final image: source + edits + annotations.
        """

        if self._editing is None:
            raise PreviewError(
                "No image is currently loaded."
            )

        return PreviewPlan(
            source=self._images[self._navigation.index],
            edits=self._editing.plan(),
            annotations=self._annotations.to_list(),
            output_size=self._editing.current_size(),
        )

    def request_export(self) -> PreviewPlan:
        """
        Transition into EXPORTING and publish the render plan
        for an export/render backend to consume.
        """

        plan = self.build_plan()

        self._transition(PreviewState.EXPORTING)

        self._publish("preview.export_requested", plan)

        return plan

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _load_current(self) -> None:

        image = self._images[self._navigation.index]

        self._viewer.load(image)

        self._editing = EditingSession(self._viewer.image_size)

        self._annotations = AnnotationLayer()

    def _refit_after_edit(self) -> None:
        """
        Keep the viewer's notion of image size in sync with the
        editing session after a size-changing operation.
        """

        width, height = self.editing.current_size()

        self._viewer.set_image_size(width, height)

    def _on_navigate(self, index: int) -> None:

        self._load_current()

        self._publish(
            "preview.navigated", {"index": index}
        )

    def _transition(self, target: PreviewState) -> None:

        allowed = _ALLOWED_TRANSITIONS.get(self._state, set())

        if target not in allowed and target != self._state:

            raise PreviewError(
                f"Cannot transition from {self._state.name} "
                f"to {target.name}."
            )

        self._state = target

    def _publish(self, event_name: str, data: Any = None) -> None:

        self._bus.publish(event_name, data)

    def __repr__(self) -> str:

        return (
            "PreviewWindow("
            f"state={self._state.name}, "
            f"images={len(self._images)}, "
            f"index={self._navigation.index}"
            ")"
        )
