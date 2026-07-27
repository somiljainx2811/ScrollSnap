"""
ScrollSnap
==========

Session Recovery

Detects unclean shutdowns (crashes, force-quits) and offers to
restore the in-progress capture session that was active at the
time.

Mechanism
---------
While a capture session is running, an "active session" marker
file is written pointing at a `.scrollsession` file on disk (see
`storage.sessions.SessionStorage`). On a clean shutdown, the
marker is removed. If the marker is still present the next time
the application starts, the previous run didn't exit cleanly, and
`check_for_recovery()` returns the session that can be restored.
"""

from __future__ import annotations

import json
from pathlib import Path

from constants import ROOT_DIR, SESSION_DIR_NAME
from models.capture_session import CaptureSession
from storage.cache import CacheStorage
from storage.sessions import SessionStorage


DEFAULT_SESSION_DIR = ROOT_DIR / SESSION_DIR_NAME

MARKER_FILENAME = ".active_session"


class SessionRecoveryManager:
    """
    Tracks the currently in-progress session and detects crash
    recovery opportunities on startup.
    """

    def __init__(
        self,
        session_dir: Path | None = None,
        session_storage: SessionStorage | None = None,
        cache_storage: CacheStorage | None = None,
    ) -> None:

        self.session_dir = session_dir or DEFAULT_SESSION_DIR

        self.session_dir.mkdir(parents=True, exist_ok=True)

        self.marker_path = self.session_dir / MARKER_FILENAME

        self.sessions = session_storage or SessionStorage()

        self.cache = cache_storage or CacheStorage()

    # ---------------------------------------------------------
    # Marking Activity
    # ---------------------------------------------------------

    def mark_active(self, session: CaptureSession) -> Path:
        """
        Persist `session` and record it as the active session.
        Call this whenever a capture session starts or its frame
        list changes meaningfully.
        """

        session_path = self.session_dir / f"{session.id}.scrollsession"

        self.sessions.save(session, session_path)

        with self.marker_path.open("w", encoding="utf-8") as handle:

            json.dump(
                {
                    "session_id": session.id,
                    "session_path": str(session_path),
                },
                handle,
            )

        return session_path

    def clear_active(self) -> None:
        """
        Call on clean shutdown (or after a successful export) to
        signal there is nothing left to recover.
        """

        if self.marker_path.exists():
            self.marker_path.unlink()

    # ---------------------------------------------------------
    # Recovery
    # ---------------------------------------------------------

    def has_pending_recovery(self) -> bool:

        return self.marker_path.exists()

    def check_for_recovery(self) -> CaptureSession | None:
        """
        Return the interrupted session if one exists and its
        session file is still readable, otherwise None.
        """

        if not self.marker_path.exists():
            return None

        try:

            with self.marker_path.open("r", encoding="utf-8") as handle:
                marker = json.load(handle)

            session_path = Path(marker["session_path"])

            if not session_path.exists():
                return None

            session = self.sessions.load(session_path)

            for frame in session.frames:
                self.cache.hydrate(frame)

            return session

        except (
            json.JSONDecodeError,
            KeyError,
            OSError,
            ValueError,
        ):
            return None

    def discard_recovery(self) -> None:
        """
        The user chose not to restore - clean up the marker and
        (best-effort) the orphaned session/cache files.
        """

        session = self.check_for_recovery()

        self.clear_active()

        if session is not None:

            self.cache.clear_session(session.id)

            session_path = (
                self.session_dir / f"{session.id}.scrollsession"
            )

            self.sessions.delete(session_path)
