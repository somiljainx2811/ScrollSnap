"""
ScrollSnap
==========

Runtime Capture Session

Represents an active capture operation.

Unlike models.capture_session.CaptureSession, this class manages
runtime state, frame collection, timing, cancellation and progress.
"""

from __future__ import annotations

from datetime import datetime
from threading import Lock

from models.capture_region import CaptureRegion
from models.frame import Frame


class RuntimeCaptureSession:
    """
    Runtime capture session.

    Thread-safe container used while a capture is running.
    """

    def __init__(
        self,
        region: CaptureRegion,
    ) -> None:

        self._lock = Lock()

        self.region = region

        self.frames: list[Frame] = []

        self.started_at = datetime.utcnow()

        self.finished_at: datetime | None = None

        self.cancelled = False

        self.completed = False

        self.paused = False

        self.frame_counter = 0

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    @property
    def running(self) -> bool:
        return (
            not self.completed
            and not self.cancelled
        )

    @property
    def duration(self) -> float:

        end = (
            self.finished_at
            if self.finished_at
            else datetime.utcnow()
        )

        return (
            end - self.started_at
        ).total_seconds()

    # ---------------------------------------------------------
    # Frames
    # ---------------------------------------------------------

    def add_frame(
        self,
        frame: Frame,
    ) -> None:
        """
        Append a captured frame.
        """

        with self._lock:

            frame.sequence = self.frame_counter

            self.frame_counter += 1

            self.frames.append(frame)

    def latest_frame(
        self,
    ) -> Frame | None:

        with self._lock:

            if not self.frames:
                return None

            return self.frames[-1]

    def clear(self) -> None:

        with self._lock:

            self.frames.clear()

            self.frame_counter = 0

    # ---------------------------------------------------------
    # Control
    # ---------------------------------------------------------

    def pause(self) -> None:
        self.paused = True

    def resume(self) -> None:
        self.paused = False

    def cancel(self) -> None:

        self.cancelled = True

        self.finished_at = datetime.utcnow()

    def finish(self) -> None:

        self.completed = True

        self.finished_at = datetime.utcnow()

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    @property
    def frames_per_second(self) -> float:

        if self.frame_count == 0:
            return 0.0

        duration = self.duration

        if duration <= 0:
            return 0.0

        return self.frame_count / duration

    @property
    def average_interval(self) -> float:

        if self.frame_count <= 1:
            return 0.0

        return self.duration / (self.frame_count - 1)

    # ---------------------------------------------------------
    # Snapshot
    # ---------------------------------------------------------

    def statistics(self) -> dict:

        return {
            "frames": self.frame_count,
            "duration": self.duration,
            "fps": self.frames_per_second,
            "average_interval": self.average_interval,
            "cancelled": self.cancelled,
            "completed": self.completed,
        }

    # ---------------------------------------------------------
    # Representation
    # ---------------------------------------------------------

    def __repr__(self) -> str:

        return (
            "RuntimeCaptureSession("
            f"frames={self.frame_count}, "
            f"duration={self.duration:.2f}s"
            ")"
        )