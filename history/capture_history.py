"""
ScrollSnap
==========

Capture History

High-level API for browsing past captures: records a thumbnail
and metadata for every completed capture/export, and lists them
back out (most recent first) for a history UI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from storage.recent_projects import RecentEntry, RecentProjectsStorage
from storage.thumbnails import ThumbnailStorage


class CaptureHistory:
    """
    Records and lists recent captures.
    """

    def __init__(
        self,
        recent: RecentProjectsStorage | None = None,
        thumbnails: ThumbnailStorage | None = None,
    ) -> None:

        self._recent = recent or RecentProjectsStorage()

        self._thumbnails = thumbnails or ThumbnailStorage()

    def record(
        self,
        image: Any,
        title: str = "Untitled Capture",
        frame_count: int = 1,
        export_path: str | Path | None = None,
    ) -> RecentEntry:
        """
        Record a completed capture in the history, generating a
        thumbnail from `image`.
        """

        entry = RecentEntry(
            title=title,
            width=getattr(image, "width", 0),
            height=getattr(image, "height", 0),
            frame_count=frame_count,
            export_path=str(export_path) if export_path else None,
        )

        thumbnail_path = self._thumbnails.generate(entry.id, image)

        entry.thumbnail_path = str(thumbnail_path)

        self._recent.add(entry)

        return entry

    def list(self) -> list[RecentEntry]:
        return self._recent.list()

    def remove(self, entry_id: str) -> None:

        self._thumbnails.delete(entry_id)

        self._recent.remove(entry_id)

    def clear(self) -> None:

        for entry in self._recent.list():
            self._thumbnails.delete(entry.id)

        self._recent.clear()
