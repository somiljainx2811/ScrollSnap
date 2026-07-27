"""
ScrollSnap
==========

Capture Engine

Main coordinator for the screenshot capture workflow.

Responsibilities
----------------
- Start and stop capture sessions
- Capture selected regions
- Manage frames
- Coordinate scheduler
- Coordinate auto-scroll
- Publish capture events

Does NOT:
- Stitch images
- Export files
- Render UI
- Perform OCR
"""

from __future__ import annotations

from datetime import datetime
from threading import Lock
from typing import Callable

from capture.capture_scheduler import CaptureScheduler
from capture.capture_session import RuntimeCaptureSession
from capture.region_manager import RegionManager
from capture.screen_capture import ScreenCapture

from capture.auto_scroll.auto_scroll_engine import (
    AutoScrollEngine,
)

from models.frame import Frame


class CaptureEngine:
    """
    Central capture controller.
    """

    def __init__(
        self,
        screen_capture: ScreenCapture,
        region_manager: RegionManager,
        scheduler: CaptureScheduler,
        auto_scroll: AutoScrollEngine | None = None,
    ) -> None:

        self._screen_capture = screen_capture

        self._region_manager = region_manager

        self._scheduler = scheduler

        self._auto_scroll = auto_scroll

        self._session: RuntimeCaptureSession | None = None

        self._listeners: list[
            Callable[[Frame], None]
        ] = []

        self._error_listeners: list[
            Callable[[Exception], None]
        ] = []

        self._lock = Lock()

        self._running = False

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def session(
        self,
    ) -> RuntimeCaptureSession | None:

        return self._session

    @property
    def running(
        self,
    ) -> bool:

        return self._running

    def set_auto_scroll(
        self,
        auto_scroll: AutoScrollEngine | None,
    ) -> None:
        """
        Attach or detach an auto-scroll engine. Must be called
        before `start()`.
        """

        self._auto_scroll = auto_scroll

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def start(
        self,
    ) -> RuntimeCaptureSession:

        region = self._region_manager.region

        if region is None:
            raise RuntimeError(
                "No capture region selected."
            )

        if self._running:
            raise RuntimeError(
                "Capture already running."
            )

        self._session = RuntimeCaptureSession(
            region
        )

        self._running = True

        self._scheduler.start(
            self.capture_once,
            on_error=self._handle_scheduler_error,
        )

        if self._auto_scroll:
            self._auto_scroll.start()

        return self._session


    def stop(
        self,
    ) -> None:

        if not self._running:
            return

        self._running = False

        self._scheduler.stop()

        if self._auto_scroll:
            self._auto_scroll.stop()

        if self._session:
            self._session.finish()


    def cancel(
        self,
    ) -> None:

        self._running = False

        self._scheduler.stop()

        if self._session:
            self._session.cancel()

    # ---------------------------------------------------------
    # Capture
    # ---------------------------------------------------------

    def capture_once(
        self,
    ) -> Frame | None:

        if not self._running:
            return None

        if self._session is None:
            return None

        if self._session.paused:
            return None


        region = self._session.region.rectangle


        image = self._screen_capture.capture_region(
            region
        )


        frame = Frame(
            image=image,
            region=region,
            timestamp=datetime.utcnow(),
        )


        with self._lock:

            self._session.add_frame(
                frame
            )


        self._notify(
            frame
        )


        return frame


    # ---------------------------------------------------------
    # Pause / Resume
    # ---------------------------------------------------------

    def pause(
        self,
    ) -> None:

        if self._session:
            self._session.pause()


    def resume(
        self,
    ) -> None:

        if self._session:
            self._session.resume()

    # ---------------------------------------------------------
    # Events
    # ---------------------------------------------------------

    def add_listener(
        self,
        callback: Callable[[Frame], None],
    ) -> None:

        if callback not in self._listeners:
            self._listeners.append(
                callback
            )


    def remove_listener(
        self,
        callback: Callable[[Frame], None],
    ) -> None:

        if callback in self._listeners:
            self._listeners.remove(
                callback
            )


    def _notify(
        self,
        frame: Frame,
    ) -> None:

        for listener in tuple(
            self._listeners
        ):
            listener(frame)

    def add_error_listener(
        self,
        callback: Callable[[Exception], None],
    ) -> None:

        if callback not in self._error_listeners:
            self._error_listeners.append(
                callback
            )

    def remove_error_listener(
        self,
        callback: Callable[[Exception], None],
    ) -> None:

        if callback in self._error_listeners:
            self._error_listeners.remove(
                callback
            )

    def _handle_scheduler_error(
        self,
        exc: Exception,
    ) -> None:
        """
        Called from the capture thread when a capture callback
        raises. Brings the engine back to a stopped state (instead
        of leaving a dead background thread and a UI that still
        thinks capture is running) and notifies listeners so the
        UI can surface the failure to the user.
        """

        self._running = False

        if self._auto_scroll:
            self._auto_scroll.stop()

        if self._session:
            self._session.finish()

        self._notify_error(exc)

    def _notify_error(
        self,
        exc: Exception,
    ) -> None:

        for listener in tuple(
            self._error_listeners
        ):
            listener(exc)