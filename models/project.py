"""
ScrollSnap
==========

Project Model

Represents a ScrollSnap project.

A project is the top-level container that groups one or more capture
sessions together with project metadata.

Projects can be saved, reopened, exported, and shared.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from models.capture_session import CaptureSession


@dataclass(slots=True)
class Project:
    """
    Represents a ScrollSnap project.
    """

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    id: str = field(default_factory=lambda: str(uuid4()))

    name: str = "Untitled Project"

    description: str = ""

    # ---------------------------------------------------------
    # Dates
    # ---------------------------------------------------------

    created_at: datetime = field(default_factory=datetime.utcnow)

    updated_at: datetime = field(default_factory=datetime.utcnow)

    # ---------------------------------------------------------
    # Sessions
    # ---------------------------------------------------------

    sessions: list[CaptureSession] = field(default_factory=list)

    active_session_index: int = 0

    # ---------------------------------------------------------
    # Storage
    # ---------------------------------------------------------

    file_path: Path | None = None

    auto_save: bool = True

    # ---------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------

    tags: list[str] = field(default_factory=list)

    metadata: dict[str, object] = field(default_factory=dict)

    # ---------------------------------------------------------
    # Session Management
    # ---------------------------------------------------------

    def add_session(
        self,
        session: CaptureSession,
    ) -> None:
        """
        Add a capture session.
        """

        self.sessions.append(session)
        self.active_session_index = len(self.sessions) - 1
        self.updated_at = datetime.utcnow()

    def remove_session(
        self,
        session: CaptureSession,
    ) -> None:
        """
        Remove a capture session.
        """

        self.sessions.remove(session)

        if self.active_session_index >= len(self.sessions):
            self.active_session_index = max(0, len(self.sessions) - 1)

        self.updated_at = datetime.utcnow()

    def clear_sessions(self) -> None:
        """
        Remove all sessions.
        """

        self.sessions.clear()
        self.active_session_index = 0
        self.updated_at = datetime.utcnow()

    # ---------------------------------------------------------
    # Convenience
    # ---------------------------------------------------------

    @property
    def active_session(self) -> CaptureSession | None:
        if not self.sessions:
            return None

        return self.sessions[self.active_session_index]

    @property
    def session_count(self) -> int:
        return len(self.sessions)

    @property
    def is_empty(self) -> bool:
        return len(self.sessions) == 0

    @property
    def total_frames(self) -> int:
        return sum(
            session.frame_count
            for session in self.sessions
        )

    # ---------------------------------------------------------
    # Serialization
    # ---------------------------------------------------------

    def to_dict(self) -> dict[str, object]:

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "sessions": [
                session.to_dict()
                for session in self.sessions
            ],
            "active_session_index": self.active_session_index,
            "file_path": (
                str(self.file_path)
                if self.file_path
                else None
            ),
            "auto_save": self.auto_save,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, object],
    ) -> "Project":

        project = cls(
            id=str(data["id"]),
            name=str(data["name"]),
            description=str(data.get("description", "")),
            created_at=datetime.fromisoformat(
                str(data["created_at"])
            ),
            updated_at=datetime.fromisoformat(
                str(data["updated_at"])
            ),
            active_session_index=int(
                data.get("active_session_index", 0)
            ),
            file_path=(
                Path(data["file_path"])
                if data.get("file_path")
                else None
            ),
            auto_save=bool(data.get("auto_save", True)),
            tags=list(data.get("tags", [])),
            metadata=dict(data.get("metadata", {})),
        )

        project.sessions = [
            CaptureSession.from_dict(session)
            for session in data.get("sessions", [])
        ]

        if project.sessions:
            project.active_session_index = min(
                project.active_session_index,
                len(project.sessions) - 1,
            )
        else:
            project.active_session_index = 0

        return project

    # ---------------------------------------------------------
    # Representation
    # ---------------------------------------------------------

    def __repr__(self) -> str:
        return (
            "Project("
            f"id={self.id!r}, "
            f"name={self.name!r}, "
            f"sessions={len(self.sessions)}"
            ")"
        )