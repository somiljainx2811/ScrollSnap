"""
ScrollSnap
==========

Recent Projects Storage

Persists a simple JSON index of recent capture/export entries:
what was captured, when, its dimensions, its thumbnail, and
where the final exported file (if any) lives.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from constants import ROOT_DIR


DEFAULT_INDEX_PATH = ROOT_DIR / "history" / "recent.json"


@dataclass(slots=True)
class RecentEntry:
    """
    One row in the capture history.
    """

    id: str = field(default_factory=lambda: str(uuid4()))

    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    title: str = "Untitled Capture"

    width: int = 0

    height: int = 0

    frame_count: int = 1

    export_path: str | None = None

    thumbnail_path: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "RecentEntry":
        return cls(**data)


class RecentProjectsStorage:
    """
    Persistent, ordered (most-recent-first) list of `RecentEntry`
    rows, capped at `max_entries`.
    """

    def __init__(
        self,
        index_path: Path | None = None,
        max_entries: int = 50,
    ) -> None:

        self.index_path = index_path or DEFAULT_INDEX_PATH

        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        self.max_entries = max_entries

    def list(self) -> list[RecentEntry]:

        if not self.index_path.exists():
            return []

        with self.index_path.open("r", encoding="utf-8") as handle:

            try:
                raw = json.load(handle)

            except json.JSONDecodeError:
                return []

        return [RecentEntry.from_dict(item) for item in raw]

    def add(self, entry: RecentEntry) -> None:

        entries = self.list()

        entries.insert(0, entry)

        entries = entries[: self.max_entries]

        self._write(entries)

    def remove(self, entry_id: str) -> None:

        entries = [e for e in self.list() if e.id != entry_id]

        self._write(entries)

    def clear(self) -> None:

        self._write([])

    def _write(self, entries: list[RecentEntry]) -> None:

        with self.index_path.open("w", encoding="utf-8") as handle:

            json.dump(
                [entry.to_dict() for entry in entries],
                handle,
                indent=2,
            )
