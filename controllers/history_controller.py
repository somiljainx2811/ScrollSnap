"""
ScrollSnap
==========

History Controller

The UI-facing entry point for capture history and crash/session
recovery.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.event_bus import EventBus, event_bus as default_event_bus
from history.capture_history import CaptureHistory
from history.recovery import SessionRecoveryManager
from models.capture_region import CaptureRegion
from models.capture_session import CaptureSession
from models.enums import CaptureStatus
from models.frame import Frame
from storage.recent_projects import RecentEntry


class HistoryController:
    """
    Coordinates capture history and session recovery.
    """

    def __init__(self, bus: EventBus | None = None) -> None:

        self._bus = bus or default_event_bus

        self._history = CaptureHistory()

        self._recovery = SessionRecoveryManager()

        self._active: CaptureSession | None = None

    # ---------------------------------------------------------
    # History
    # ---------------------------------------------------------

    def record_capture(
        self,
        image: Any,
        title: str = "Untitled Capture",
        frame_count: int = 1,
        export_path: str | Path | None = None,
    ) -> RecentEntry:

        entry = self._history.record(
            image,
            title=title,
            frame_count=frame_count,
            export_path=export_path,
        )

        self._bus.publish("history.recorded", entry)

        return entry

    def recent_entries(self) -> list[RecentEntry]:
        return self._history.list()

    def remove_entry(self, entry_id: str) -> None:
        self._history.remove(entry_id)

    def clear_history(self) -> None:
        self._history.clear()

    # ---------------------------------------------------------
    # Session Recovery
    # ---------------------------------------------------------

    def begin_session(self, region: CaptureRegion | None) -> CaptureSession:
        """
        Start tracking a new in-progress capture session for
        crash recovery.
        """

        self._active = CaptureSession(
            region=region, status=CaptureStatus.CAPTURING
        )

        self._recovery.mark_active(self._active)

        return self._active

    def track_frame(self, frame: Frame) -> None:
        """
        Cache a newly captured frame's pixels and refresh the
        on-disk recovery snapshot. Call this from a capture
        frame listener.
        """

        if self._active is None:
            return

        self._recovery.cache.save_frame(self._active.id, frame)

        self._active.add_frame(frame)

        self._recovery.mark_active(self._active)

    def end_session(self) -> None:
        """
        Call once a session has been successfully stitched/
        exported - there is nothing left to recover.
        """

        if self._active is not None:
            self._recovery.cache.clear_session(self._active.id)

        self._active = None

        self._recovery.clear_active()

    def clear_active_session(self) -> None:
        self._recovery.clear_active()

    def has_pending_recovery(self) -> bool:
        return self._recovery.has_pending_recovery()

    def recover_session(self) -> CaptureSession | None:
        return self._recovery.check_for_recovery()

    def discard_recovery(self) -> None:
        self._recovery.discard_recovery()
