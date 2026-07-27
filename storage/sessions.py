"""
ScrollSnap
==========

Session Storage

Persistent storage for CaptureSession objects.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models.capture_session import CaptureSession


DEFAULT_EXTENSION = ".scrollsession"


class SessionStorage:
    """
    Handles persistence of CaptureSession objects.
    """

    def save(
        self,
        session: CaptureSession,
        path: str | Path,
    ) -> None:
        """
        Save a capture session.
        """

        path = Path(path)

        if path.suffix == "":
            path = path.with_suffix(DEFAULT_EXTENSION)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                session.to_dict(),
                file,
                indent=4,
                ensure_ascii=False,
            )

    def load(
        self,
        path: str | Path,
    ) -> CaptureSession:
        """
        Load a capture session.
        """

        path = Path(path)

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data: dict[str, Any] = json.load(file)

        return CaptureSession.from_dict(data)

    def exists(
        self,
        path: str | Path,
    ) -> bool:
        """
        Returns True if a session file exists.
        """

        return Path(path).exists()

    def delete(
        self,
        path: str | Path,
    ) -> None:
        """
        Delete a session file.
        """

        path = Path(path)

        if path.exists():
            path.unlink()

    def duplicate(
        self,
        source: str | Path,
        destination: str | Path,
    ) -> None:
        """
        Duplicate a session.
        """

        session = self.load(source)

        self.save(
            session,
            destination,
        )

    def rename(
        self,
        source: str | Path,
        destination: str | Path,
    ) -> None:
        """
        Rename or move a session file.
        """

        source = Path(source)
        destination = Path(destination)

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        source.rename(destination)