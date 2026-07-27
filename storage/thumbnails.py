"""
ScrollSnap
==========

Thumbnail Storage

Generates and persists small preview thumbnails for capture
history entries, so the history browser doesn't need to decode
full-resolution images just to show a list.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image

from constants import ROOT_DIR, THUMBNAIL_DIR_NAME


DEFAULT_THUMBNAIL_DIR = ROOT_DIR / THUMBNAIL_DIR_NAME

DEFAULT_SIZE = (240, 180)


class ThumbnailStorage:
    """
    Manages on-disk thumbnails.
    """

    def __init__(
        self,
        thumbnail_dir: Path | None = None,
        size: tuple[int, int] = DEFAULT_SIZE,
    ) -> None:

        self.thumbnail_dir = thumbnail_dir or DEFAULT_THUMBNAIL_DIR

        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)

        self.size = size

    def generate(self, entry_id: str, image: Any) -> Path:
        """
        Create and save a thumbnail for `image`, returning the
        path it was written to.
        """

        thumbnail = image.convert("RGB").copy()

        thumbnail.thumbnail(self.size, Image.LANCZOS)

        path = self.thumbnail_dir / f"{entry_id}.jpg"

        thumbnail.save(path, "JPEG", quality=80)

        return path

    def load(self, entry_id: str) -> Image.Image | None:

        path = self.thumbnail_dir / f"{entry_id}.jpg"

        if not path.exists():
            return None

        return Image.open(path)

    def path_for(self, entry_id: str) -> Path:
        return self.thumbnail_dir / f"{entry_id}.jpg"

    def delete(self, entry_id: str) -> None:

        path = self.path_for(entry_id)

        if path.exists():
            path.unlink()
