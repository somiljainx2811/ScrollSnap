"""
ScrollSnap
==========

Cache Storage

Persists frame and preview pixel data to disk.

`models.frame.Frame` deliberately keeps `image` as an in-memory,
backend-agnostic `Any` and never serializes it directly (see
`Frame.to_dict()`) - only `cache_path` is persisted. This module
is what actually writes those cache files and reloads them, which
is what makes session save/restore and crash recovery meaningful
rather than metadata-only.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from constants import CACHE_DIR_NAME, ROOT_DIR
from models.frame import Frame


DEFAULT_CACHE_DIR = ROOT_DIR / CACHE_DIR_NAME


class CacheStorage:
    """
    Manages the on-disk image cache for frames and sessions.
    """

    def __init__(self, cache_dir: Path | None = None) -> None:

        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR

        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # Frames
    # ---------------------------------------------------------

    def save_frame(self, session_id: str, frame: Frame) -> Path:
        """
        Persist a frame's pixel data to the cache, and record the
        resulting path on the frame itself (`frame.cache_path`).
        """

        if frame.image is None:
            raise ValueError("Frame has no image to cache.")

        session_dir = self.cache_dir / session_id

        session_dir.mkdir(parents=True, exist_ok=True)

        path = session_dir / f"{frame.id}.png"

        frame.image.save(path, "PNG")

        frame.cache_path = path

        return path

    def load_frame_image(self, frame: Frame) -> Image.Image:
        """
        Load a frame's cached pixel data back into memory. Does
        not mutate `frame.image` - the caller decides whether to
        assign it.
        """

        if frame.cache_path is None:
            raise ValueError("Frame has no cache_path to load.")

        return Image.open(frame.cache_path).convert("RGB")

    def hydrate(self, frame: Frame) -> Frame:
        """
        Load the cached image back into `frame.image` if it isn't
        already populated, returning the same frame for chaining.
        """

        if frame.image is None and frame.cache_path is not None:
            frame.image = self.load_frame_image(frame)

        return frame

    # ---------------------------------------------------------
    # Session Cleanup
    # ---------------------------------------------------------

    def session_dir(self, session_id: str) -> Path:
        return self.cache_dir / session_id

    def clear_session(self, session_id: str) -> None:
        """
        Delete every cached frame belonging to a session.
        """

        session_dir = self.session_dir(session_id)

        if not session_dir.exists():
            return

        for item in session_dir.iterdir():
            item.unlink()

        session_dir.rmdir()

    def total_size_bytes(self) -> int:

        return sum(
            path.stat().st_size
            for path in self.cache_dir.rglob("*")
            if path.is_file()
        )

    def clear_all(self) -> None:

        for item in self.cache_dir.iterdir():

            if item.is_dir():

                for sub in item.iterdir():
                    sub.unlink()

                item.rmdir()

            else:
                item.unlink()
