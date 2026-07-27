"""
ScrollSnap
==========

Frame Model

Represents a single captured frame together with its metadata.

A Frame is the fundamental unit produced by the capture engine and
consumed by the stitching engine, preview, OCR, export, and history.

The image itself is intentionally stored as `Any` to avoid coupling this
model to a specific imaging library (Pillow, OpenCV, NumPy, Qt, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from models.rectangle import Rectangle


@dataclass(slots=True)
class Frame:
    """
    Represents one captured frame.
    """

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    id: str = field(default_factory=lambda: str(uuid4()))

    # ---------------------------------------------------------
    # Image
    # ---------------------------------------------------------

    image: Any = None

    thumbnail: Any = None

    # ---------------------------------------------------------
    # Geometry
    # ---------------------------------------------------------

    region: Rectangle = field(default_factory=Rectangle.empty)

    # ---------------------------------------------------------
    # Timing
    # ---------------------------------------------------------

    timestamp: datetime = field(default_factory=datetime.utcnow)

    sequence: int = 0

    # ---------------------------------------------------------
    # Capture Metadata
    # ---------------------------------------------------------

    monitor_id: int = 0

    scroll_offset: int = 0

    dpi_scale: float = 1.0

    # ---------------------------------------------------------
    # Processing Metadata
    # ---------------------------------------------------------

    overlap_score: float = 0.0

    hash: str | None = None

    duplicate: bool = False

    stitched: bool = False

    # ---------------------------------------------------------
    # Storage
    # ---------------------------------------------------------

    source_path: Path | None = None

    cache_path: Path | None = None

    # ---------------------------------------------------------
    # Custom Metadata
    # ---------------------------------------------------------

    metadata: dict[str, object] = field(default_factory=dict)

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def __post_init__(self) -> None:

        if self.sequence < 0:
            raise ValueError(
                "sequence must be non-negative."
            )

        if self.monitor_id < 0:
            raise ValueError(
                "monitor_id must be non-negative."
            )

        if self.dpi_scale <= 0:
            raise ValueError(
                "dpi_scale must be positive."
            )

    # ---------------------------------------------------------
    # Convenience
    # ---------------------------------------------------------

    @property
    def width(self) -> float:
        return self.region.width

    @property
    def height(self) -> float:
        return self.region.height

    @property
    def area(self) -> float:
        return self.region.area

    @property
    def has_image(self) -> bool:
        return self.image is not None

    @property
    def has_thumbnail(self) -> bool:
        return self.thumbnail is not None

    @property
    def is_duplicate(self) -> bool:
        return self.duplicate

    @property
    def is_stitched(self) -> bool:
        return self.stitched

    # ---------------------------------------------------------
    # Serialization
    # ---------------------------------------------------------

    def to_dict(self) -> dict[str, object]:

        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "sequence": self.sequence,
            "monitor_id": self.monitor_id,
            "scroll_offset": self.scroll_offset,
            "dpi_scale": self.dpi_scale,
            "region": self.region.to_dict(),
            "overlap_score": self.overlap_score,
            "hash": self.hash,
            "duplicate": self.duplicate,
            "stitched": self.stitched,
            "source_path": (
                str(self.source_path)
                if self.source_path
                else None
            ),
            "cache_path": (
                str(self.cache_path)
                if self.cache_path
                else None
            ),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, object],
    ) -> "Frame":

        source = data.get("source_path")
        cache = data.get("cache_path")

        return cls(
            id=str(data["id"]),
            region=Rectangle.from_dict(
                data["region"]  # type: ignore[arg-type]
            ),
            timestamp=datetime.fromisoformat(
                str(data["timestamp"])
            ),
            sequence=int(data["sequence"]),
            monitor_id=int(data["monitor_id"]),
            scroll_offset=int(data["scroll_offset"]),
            dpi_scale=float(data["dpi_scale"]),
            overlap_score=float(data["overlap_score"]),
            hash=data.get("hash"),
            duplicate=bool(data["duplicate"]),
            stitched=bool(data["stitched"]),
            source_path=Path(source) if source else None,
            cache_path=Path(cache) if cache else None,
            metadata=dict(data.get("metadata", {})),
        )

    # ---------------------------------------------------------
    # Utility
    # ---------------------------------------------------------

    def mark_duplicate(self) -> None:
        """
        Mark this frame as a duplicate.
        """
        self.duplicate = True

    def mark_stitched(self) -> None:
        """
        Mark this frame as stitched.
        """
        self.stitched = True

    def __repr__(self) -> str:

        return (
            "Frame("
            f"id={self.id!r}, "
            f"sequence={self.sequence}, "
            f"region={self.region!r}, "
            f"duplicate={self.duplicate}, "
            f"stitched={self.stitched}"
            ")"
        )