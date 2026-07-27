"""
ScrollSnap
==========

Capture Session Model

Represents a complete capture operation from start to finish.

A CaptureSession owns:
    - Capture region
    - Captured frames
    - Export options
    - Session metadata
    - Timing information

This is the primary aggregate for the capture pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from models.capture_region import CaptureRegion
from models.enums import CaptureStatus
from models.export_options import ExportOptions
from models.frame import Frame


@dataclass(slots=True)
class CaptureSession:
    """
    Represents one capture session.
    """

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    id: str = field(default_factory=lambda: str(uuid4()))

    name: str = "Untitled Capture"

    created_at: datetime = field(default_factory=datetime.utcnow)

    updated_at: datetime = field(default_factory=datetime.utcnow)

    status: CaptureStatus = CaptureStatus.IDLE

    # ---------------------------------------------------------
    # Capture
    # ---------------------------------------------------------

    region: CaptureRegion | None = None

    frames: list[Frame] = field(default_factory=list)

    # ---------------------------------------------------------
    # Export
    # ---------------------------------------------------------

    export_options: ExportOptions = field(
        default_factory=ExportOptions
    )

    # ---------------------------------------------------------
    # Storage
    # ---------------------------------------------------------

    project_path: Path | None = None

    # ---------------------------------------------------------
    # User Metadata
    # ---------------------------------------------------------

    tags: list[str] = field(default_factory=list)

    metadata: dict[str, object] = field(default_factory=dict)

    # ---------------------------------------------------------
    # Frame Operations
    # ---------------------------------------------------------

    def add_frame(self, frame: Frame) -> None:
        """
        Add a frame to the session.
        """

        frame.sequence = len(self.frames)

        self.frames.append(frame)

        self.updated_at = datetime.utcnow()

    def remove_frame(
        self,
        frame: Frame,
    ) -> None:
        """
        Remove a frame.
        """

        self.frames.remove(frame)

        self.updated_at = datetime.utcnow()

        for index, item in enumerate(self.frames):
            item.sequence = index

    def clear_frames(self) -> None:
        """
        Remove every frame.
        """

        self.frames.clear()

        self.updated_at = datetime.utcnow()

    # ---------------------------------------------------------
    # Convenience
    # ---------------------------------------------------------

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    @property
    def is_empty(self) -> bool:
        return len(self.frames) == 0

    @property
    def first_frame(self) -> Frame | None:
        if self.frames:
            return self.frames[0]
        return None

    @property
    def last_frame(self) -> Frame | None:
        if self.frames:
            return self.frames[-1]
        return None

    @property
    def has_region(self) -> bool:
        return self.region is not None

    # ---------------------------------------------------------
    # Status
    # ---------------------------------------------------------

    def set_status(
        self,
        status: CaptureStatus,
    ) -> None:
        """
        Update session status.
        """

        self.status = status

        self.updated_at = datetime.utcnow()

    # ---------------------------------------------------------
    # Serialization
    # ---------------------------------------------------------

    def to_dict(self) -> dict[str, object]:

        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status.name,
            "region": (
                self.region.to_dict()
                if self.region
                else None
            ),
            "frames": [
                frame.to_dict()
                for frame in self.frames
            ],
            "export_options":
                self.export_options.to_dict(),
            "project_path": (
                str(self.project_path)
                if self.project_path
                else None
            ),
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, object],
    ) -> "CaptureSession":

        session = cls(
            id=str(data["id"]),
            name=str(data["name"]),
            created_at=datetime.fromisoformat(
                str(data["created_at"])
            ),
            updated_at=datetime.fromisoformat(
                str(data["updated_at"])
            ),
            status=CaptureStatus[
                str(data["status"])
            ],
            region=(
                CaptureRegion.from_dict(data["region"])
                if data.get("region")
                else None
            ),
            export_options=ExportOptions.from_dict(
                data["export_options"]
            ),
            project_path=(
                Path(data["project_path"])
                if data.get("project_path")
                else None
            ),
            tags=list(data.get("tags", [])),
            metadata=dict(
                data.get("metadata", {})
            ),
        )

        session.frames = [
            Frame.from_dict(frame)
            for frame in data.get("frames", [])
        ]

        return session

    # ---------------------------------------------------------
    # Representation
    # ---------------------------------------------------------

    def __repr__(self) -> str:
        return (
            "CaptureSession("
            f"id={self.id!r}, "
            f"name={self.name!r}, "
            f"status={self.status.name}, "
            f"frames={len(self.frames)}"
            ")"
        )