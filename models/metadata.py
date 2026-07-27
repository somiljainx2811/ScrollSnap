"""
ScrollSnap
==========

Metadata Model

Defines common metadata attached to projects, sessions, frames,
and exported files.

This model provides a structured alternative to arbitrary
metadata dictionaries while still allowing custom user or plugin
properties.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class Metadata:
    """
    Common metadata container.
    """

    # ---------------------------------------------------------
    # Versioning
    # ---------------------------------------------------------

    schema_version: int = 1

    application_version: str = "1.0.0"

    # ---------------------------------------------------------
    # Dates
    # ---------------------------------------------------------

    created_at: datetime = field(default_factory=datetime.utcnow)

    modified_at: datetime = field(default_factory=datetime.utcnow)

    # ---------------------------------------------------------
    # Attribution
    # ---------------------------------------------------------

    author: str = ""

    description: str = ""

    source: str = ""

    tags: list[str] = field(default_factory=list)

    # ---------------------------------------------------------
    # Plugin / Extension Data
    # ---------------------------------------------------------

    custom: dict[str, Any] = field(default_factory=dict)

    # ---------------------------------------------------------
    # Convenience
    # ---------------------------------------------------------

    def touch(self) -> None:
        """
        Update modification timestamp.
        """

        self.modified_at = datetime.utcnow()

    def add_tag(self, tag: str) -> None:
        """
        Add a tag if not already present.
        """

        tag = tag.strip()

        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.touch()

    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag.
        """

        if tag in self.tags:
            self.tags.remove(tag)
            self.touch()

    # ---------------------------------------------------------
    # Serialization
    # ---------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "application_version": self.application_version,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "author": self.author,
            "description": self.description,
            "source": self.source,
            "tags": list(self.tags),
            "custom": dict(self.custom),
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "Metadata":

        return cls(
            schema_version=int(
                data.get("schema_version", 1)
            ),
            application_version=str(
                data.get("application_version", "1.0.0")
            ),
            created_at=datetime.fromisoformat(
                str(data["created_at"])
            )
            if "created_at" in data
            else datetime.utcnow(),
            modified_at=datetime.fromisoformat(
                str(data["modified_at"])
            )
            if "modified_at" in data
            else datetime.utcnow(),
            author=str(data.get("author", "")),
            description=str(data.get("description", "")),
            source=str(data.get("source", "")),
            tags=list(data.get("tags", [])),
            custom=dict(data.get("custom", {})),
        )

    def copy(self) -> "Metadata":
        """
        Create a deep copy.
        """

        return Metadata.from_dict(self.to_dict())

    def __repr__(self) -> str:
        return (
            "Metadata("
            f"schema_version={self.schema_version}, "
            f"author={self.author!r}, "
            f"tags={len(self.tags)}"
            ")"
        )