"""
ScrollSnap
==========

Capture Region Model

Represents a user-selected capture region together with all metadata
required by the capture engine.

Unlike Rectangle, this class contains domain-specific information such as
capture mode, selection shape, monitor information, DPI scaling and
auto-scroll options.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from models.enums import CaptureMode, ShapeType
from models.rectangle import Rectangle


@dataclass(frozen=True, slots=True)
class CaptureRegion:
    """
    Represents a capture region.

    Parameters
    ----------
    rectangle
        Bounding rectangle of the capture region.

    shape
        Selection shape.

    mode
        Capture mode.

    monitor_id
        Monitor index.

    dpi_scale
        Monitor DPI scaling.

    auto_scroll
        Whether auto scrolling is enabled.

    include_cursor
        Capture mouse cursor.

    include_shadow
        Include window shadow.

    locked
        Region cannot be resized.
    """

    rectangle: Rectangle

    shape: ShapeType = ShapeType.RECTANGLE

    mode: CaptureMode = CaptureMode.REGION

    monitor_id: int = 0

    dpi_scale: float = 1.0

    auto_scroll: bool = False

    include_cursor: bool = False

    include_shadow: bool = False

    locked: bool = False

    metadata: dict[str, object] = field(default_factory=dict)

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def __post_init__(self) -> None:

        if self.monitor_id < 0:
            raise ValueError(
                "monitor_id cannot be negative."
            )

        if self.dpi_scale <= 0:
            raise ValueError(
                "dpi_scale must be positive."
            )

    # ---------------------------------------------------------
    # Geometry
    # ---------------------------------------------------------

    @property
    def left(self):
        return self.rectangle.left

    @property
    def top(self):
        return self.rectangle.top

    @property
    def right(self):
        return self.rectangle.right

    @property
    def bottom(self):
        return self.rectangle.bottom

    @property
    def width(self):
        return self.rectangle.width

    @property
    def height(self):
        return self.rectangle.height

    @property
    def center(self):
        return self.rectangle.center

    @property
    def area(self):
        return self.rectangle.area

    # ---------------------------------------------------------
    # Convenience
    # ---------------------------------------------------------

    @property
    def is_scrolling_capture(self) -> bool:
        return (
            self.mode == CaptureMode.SCROLLING
        )

    @property
    def is_rectangular(self) -> bool:
        return (
            self.shape == ShapeType.RECTANGLE
        )

    @property
    def has_custom_shape(self) -> bool:
        return (
            self.shape
            != ShapeType.RECTANGLE
        )

    # ---------------------------------------------------------
    # Transformations
    # ---------------------------------------------------------

    def translate(
        self,
        dx: float,
        dy: float,
    ) -> "CaptureRegion":
        """
        Returns translated region.
        """

        return CaptureRegion(
            rectangle=self.rectangle.translate(dx, dy),
            shape=self.shape,
            mode=self.mode,
            monitor_id=self.monitor_id,
            dpi_scale=self.dpi_scale,
            auto_scroll=self.auto_scroll,
            include_cursor=self.include_cursor,
            include_shadow=self.include_shadow,
            locked=self.locked,
            metadata=dict(self.metadata),
        )

    def replace_rectangle(
        self,
        rectangle: Rectangle,
    ) -> "CaptureRegion":
        """
        Returns identical region with another rectangle.
        """

        return CaptureRegion(
            rectangle=rectangle,
            shape=self.shape,
            mode=self.mode,
            monitor_id=self.monitor_id,
            dpi_scale=self.dpi_scale,
            auto_scroll=self.auto_scroll,
            include_cursor=self.include_cursor,
            include_shadow=self.include_shadow,
            locked=self.locked,
            metadata=dict(self.metadata),
        )

    # ---------------------------------------------------------
    # Serialization
    # ---------------------------------------------------------

    def to_dict(self) -> dict:
        """
        Serialize region.
        """

        return {
            "rectangle": self.rectangle.to_dict(),
            "shape": self.shape.name,
            "mode": self.mode.name,
            "monitor_id": self.monitor_id,
            "dpi_scale": self.dpi_scale,
            "auto_scroll": self.auto_scroll,
            "include_cursor": self.include_cursor,
            "include_shadow": self.include_shadow,
            "locked": self.locked,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict,
    ) -> "CaptureRegion":

        return cls(
            rectangle=Rectangle.from_dict(
                data["rectangle"]
            ),
            shape=ShapeType[data["shape"]],
            mode=CaptureMode[data["mode"]],
            monitor_id=data.get(
                "monitor_id",
                0,
            ),
            dpi_scale=data.get(
                "dpi_scale",
                1.0,
            ),
            auto_scroll=data.get(
                "auto_scroll",
                False,
            ),
            include_cursor=data.get(
                "include_cursor",
                False,
            ),
            include_shadow=data.get(
                "include_shadow",
                False,
            ),
            locked=data.get(
                "locked",
                False,
            ),
            metadata=dict(
                data.get(
                    "metadata",
                    {},
                )
            ),
        )

    # ---------------------------------------------------------
    # Copy Helpers
    # ---------------------------------------------------------

    def copy(self) -> "CaptureRegion":
        """
        Returns identical region.
        """

        return self.replace_rectangle(
            self.rectangle.copy()
        )

    # ---------------------------------------------------------
    # String Representation
    # ---------------------------------------------------------

    def __repr__(self) -> str:

        return (
            "CaptureRegion("
            f"rectangle={self.rectangle!r}, "
            f"shape={self.shape.name}, "
            f"mode={self.mode.name}, "
            f"monitor={self.monitor_id}"
            ")"
        )