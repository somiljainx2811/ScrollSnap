"""
ScrollSnap
==========

MSS Screen Capture Backend

Concrete, cross-platform implementation of
`capture.screen_capture.ScreenCapture` using the `mss` library.

`mss` supports Windows, macOS, and Linux (X11) through a single
API, so unlike input injection and window detection, screen
capture does not need per-OS subclasses.

Note: package is named `platforms/` (plural), not `platform/`,
to avoid shadowing Python's standard library `platform` module,
which several parts of this project (and `mss` itself) rely on.
"""

from __future__ import annotations

import threading

from PIL import Image

from capture.screen_capture import ScreenCapture
from models.rectangle import Rectangle
from platforms.mss_compat import create_mss


class MssScreenCapture(ScreenCapture):
    """
    Screen capture backend built on top of `mss`.

    Thread-safety note
    -------------------
    `mss` instances are thread-affine: on Windows, the GDI device
    contexts an instance grabs (`GetWindowDC`/`CreateCompatibleDC`)
    are only valid on the thread that created them. Using one
    `mss` instance from a different thread than it was constructed
    on fails with `AttributeError: '_thread._local' object has no
    attribute 'srcdc'` (mss keeps that handle in its own
    thread-local storage, and the calling thread never populated
    it).

    ScrollSnap constructs this class on the main/UI thread but
    calls `capture_region()` from the background capture-scheduler
    thread during a scrolling capture, so a single shared `mss`
    instance is not safe here - each thread that ends up calling
    into this class gets its own lazily-created `mss` instance via
    `threading.local()`.
    """

    def __init__(self) -> None:

        self._local = threading.local()

        self._instances: list = []

        self._instances_lock = threading.Lock()

    @property
    def _sct(self):

        sct = getattr(self._local, "sct", None)

        if sct is None:

            sct = create_mss()

            self._local.sct = sct

            with self._instances_lock:
                self._instances.append(sct)

        return sct

    # ---------------------------------------------------------
    # Capture
    # ---------------------------------------------------------

    def capture_region(self, region: Rectangle) -> Image.Image:

        bounding_box = {
            "left": int(region.left),
            "top": int(region.top),
            "width": max(1, int(region.width)),
            "height": max(1, int(region.height)),
        }

        shot = self._sct.grab(bounding_box)

        return Image.frombytes(
            "RGB", shot.size, shot.rgb
        )

    def capture_monitor(self, monitor_id: int) -> Image.Image:

        monitor = self._monitor(monitor_id)

        shot = self._sct.grab(monitor)

        return Image.frombytes(
            "RGB", shot.size, shot.rgb
        )

    def capture_window(self, window_handle: int) -> Image.Image:
        """
        `mss` has no native window-capture call, so this
        approximates it by capturing the window's bounds on
        the monitor it belongs to. Callers needing pixel-exact
        window capture (excluding overlapping windows) should
        prefer `capture_region` with geometry from a
        `WindowDetector`.
        """

        raise NotImplementedError(
            "Direct window-handle capture is not supported by "
            "the mss backend; use capture_region() with the "
            "window's bounds from a WindowDetector instead."
        )

    # ---------------------------------------------------------
    # Monitors
    # ---------------------------------------------------------

    def monitor_count(self) -> int:

        # index 0 is the "all monitors combined" virtual screen
        return max(0, len(self._sct.monitors) - 1)

    def monitor_geometry(self, monitor_id: int) -> Rectangle:

        monitor = self._monitor(monitor_id)

        return Rectangle.from_xywh(
            monitor["left"],
            monitor["top"],
            monitor["width"],
            monitor["height"],
        )

    def _monitor(self, monitor_id: int) -> dict:

        monitors = self._sct.monitors

        index = monitor_id + 1  # skip the "combined" entry

        if not (0 <= index < len(monitors)):
            raise ValueError(
                f"No monitor with id {monitor_id}."
            )

        return monitors[index]

    def close(self) -> None:

        with self._instances_lock:
            instances, self._instances = self._instances, []

        for sct in instances:
            sct.close()

    def __repr__(self) -> str:

        return (
            f"MssScreenCapture(monitors={self.monitor_count()})"
        )
