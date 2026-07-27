"""
ScrollSnap
==========

Window Detectors

Concrete, per-OS implementations of
`capture.auto_scroll.window_detector.WindowDetector`:

    LinuxWindowDetector   - X11 via python-xlib (EWMH hints)
    WindowsWindowDetector - Win32 API via ctypes
    NullWindowDetector    - safe no-op fallback

Window detection is the one piece of the capture pipeline that
is inherently OS-specific (unlike screen capture and input
injection, which `mss`/`pynput` already abstract), so it keeps
one implementation per platform.
"""

from __future__ import annotations

import sys

from capture.auto_scroll.window_detector import (
    WindowDetector,
    WindowInfo,
)
from models.rectangle import Rectangle


class NullWindowDetector(WindowDetector):
    """
    Safe fallback used when no OS-specific backend is available.

    Auto-scroll and capture still work without window tracking
    (input is injected at the current cursor position, not
    targeted at a window handle) - this detector simply means
    the app can't report window titles/geometry or
    bring a window to the foreground automatically.
    """

    def active_window(self) -> WindowInfo | None:
        return None

    def window_from_point(self, x: int, y: int) -> WindowInfo | None:
        return None

    def window_from_handle(self, handle: int) -> WindowInfo | None:
        return None

    def enumerate_windows(self) -> list[WindowInfo]:
        return []

    def refresh(self, window: WindowInfo) -> WindowInfo:
        return window


class LinuxWindowDetector(WindowDetector):
    """
    X11 window detector using python-xlib and the standard EWMH
    (Extended Window Manager Hints) root-window properties.

    Requires a running, EWMH-compliant window manager.
    """

    def __init__(self) -> None:

        from Xlib import display

        self._display = display.Display()

        self._root = self._display.screen().root

        self._atoms: dict[str, int] = {}

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def active_window(self) -> WindowInfo | None:

        window_id = self._get_property(
            self._root, "_NET_ACTIVE_WINDOW"
        )

        if not window_id:
            return None

        return self._describe(window_id[0])

    def window_from_point(self, x: int, y: int) -> WindowInfo | None:

        from Xlib.ext import xtest  # noqa: F401  (ensures extension loaded)

        pointer_window = self._root.query_pointer().child

        if pointer_window is None or pointer_window.id == 0:
            return self.active_window()

        return self._describe(pointer_window.id)

    def window_from_handle(self, handle: int) -> WindowInfo | None:
        return self._describe(handle)

    def enumerate_windows(self) -> list[WindowInfo]:

        client_list = self._get_property(
            self._root, "_NET_CLIENT_LIST"
        )

        if not client_list:
            return []

        windows = []

        for window_id in client_list:

            info = self._describe(window_id)

            if info is not None:
                windows.append(info)

        return windows

    def refresh(self, window: WindowInfo) -> WindowInfo:

        updated = self._describe(window.handle)

        return updated if updated is not None else window

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _atom(self, name: str) -> int:

        if name not in self._atoms:
            self._atoms[name] = self._display.intern_atom(name)

        return self._atoms[name]

    def _get_property(self, window, name: str):

        try:

            prop = window.get_full_property(
                self._atom(name), 0
            )

        except Exception:
            return None

        if prop is None:
            return None

        return list(prop.value)

    def _describe(self, window_id: int) -> WindowInfo | None:

        try:

            window = self._display.create_resource_object(
                "window", window_id
            )

            geometry = window.get_geometry()

            translated = window.translate_coords(
                self._root, 0, 0
            )

            title = self._window_title(window)

            wm_class = window.get_wm_class()

            class_name = wm_class[1] if wm_class else ""

            pid_prop = self._get_property(window, "_NET_WM_PID")

            pid = pid_prop[0] if pid_prop else 0

            process_name = self._process_name(pid)

            bounds = Rectangle.from_xywh(
                -translated.x,
                -translated.y,
                geometry.width,
                geometry.height,
            )

            return WindowInfo(
                handle=window_id,
                title=title,
                class_name=class_name,
                process_name=process_name,
                process_id=pid,
                bounds=bounds,
            )

        except Exception:
            return None

    def _window_title(self, window) -> str:

        for atom_name in ("_NET_WM_NAME", "WM_NAME"):

            prop = self._get_property(window, atom_name)

            if prop:

                try:
                    return bytes(prop).decode(
                        "utf-8", errors="replace"
                    )

                except TypeError:
                    return str(prop)

        return ""

    def _process_name(self, pid: int) -> str:

        if not pid:
            return ""

        try:

            with open(f"/proc/{pid}/comm", "r") as handle:
                return handle.read().strip()

        except OSError:
            return ""


class WindowsWindowDetector(WindowDetector):
    """
    Win32 window detector using ctypes (no pywin32 dependency).
    """

    def __init__(self) -> None:

        import ctypes
        from ctypes import wintypes

        self._ctypes = ctypes

        self._wintypes = wintypes

        self._user32 = ctypes.windll.user32

        self._kernel32 = ctypes.windll.kernel32

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def active_window(self) -> WindowInfo | None:

        handle = self._user32.GetForegroundWindow()

        return self._describe(handle)

    def window_from_point(self, x: int, y: int) -> WindowInfo | None:

        point = self._wintypes.POINT(x, y)

        handle = self._user32.WindowFromPoint(point)

        top_level = self._user32.GetAncestor(handle, 2)  # GA_ROOT

        return self._describe(top_level or handle)

    def window_from_handle(self, handle: int) -> WindowInfo | None:
        return self._describe(handle)

    def enumerate_windows(self) -> list[WindowInfo]:

        ctypes = self._ctypes

        handles: list[int] = []

        WNDENUMPROC = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.c_void_p,
            ctypes.c_void_p,
        )

        def _callback(hwnd, _lparam):
            handles.append(hwnd)
            return True

        self._user32.EnumWindows(WNDENUMPROC(_callback), 0)

        windows = []

        for handle in handles:

            if not self._user32.IsWindowVisible(handle):
                continue

            info = self._describe(handle)

            if info is not None:
                windows.append(info)

        return windows

    def refresh(self, window: WindowInfo) -> WindowInfo:

        updated = self._describe(window.handle)

        return updated if updated is not None else window

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _describe(self, handle: int) -> WindowInfo | None:

        if not handle:
            return None

        ctypes = self._ctypes

        wintypes = self._wintypes

        length = self._user32.GetWindowTextLengthW(handle) + 1

        buffer = ctypes.create_unicode_buffer(length)

        self._user32.GetWindowTextW(handle, buffer, length)

        class_buffer = ctypes.create_unicode_buffer(256)

        self._user32.GetClassNameW(handle, class_buffer, 256)

        rect = wintypes.RECT()

        self._user32.GetWindowRect(handle, ctypes.byref(rect))

        pid = wintypes.DWORD()

        self._user32.GetWindowThreadProcessId(
            handle, ctypes.byref(pid)
        )

        return WindowInfo(
            handle=handle,
            title=buffer.value,
            class_name=class_buffer.value,
            process_name=self._process_name(pid.value),
            process_id=pid.value,
            bounds=Rectangle(
                rect.left, rect.top, rect.right, rect.bottom
            ),
            visible=bool(self._user32.IsWindowVisible(handle)),
            minimized=bool(self._user32.IsIconic(handle)),
            maximized=bool(self._user32.IsZoomed(handle)),
        )

    def _process_name(self, pid: int) -> str:

        if not pid:
            return ""

        ctypes = self._ctypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

        handle = self._kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid
        )

        if not handle:
            return ""

        try:

            buffer = ctypes.create_unicode_buffer(260)

            size = ctypes.c_uint(260)

            psapi = ctypes.windll.kernel32

            if psapi.QueryFullProcessImageNameW(
                handle, 0, buffer, ctypes.byref(size)
            ):
                return buffer.value.rsplit("\\", 1)[-1]

            return ""

        finally:
            self._kernel32.CloseHandle(handle)


# ---------------------------------------------------------
# Factory
# ---------------------------------------------------------

def create_window_detector() -> WindowDetector:
    """
    Return the best available `WindowDetector` for the current
    platform, falling back to `NullWindowDetector` if the
    platform-specific backend can't be constructed (e.g. no X
    display, or a headless CI environment).
    """

    if sys.platform.startswith("win"):

        try:
            return WindowsWindowDetector()

        except Exception:
            return NullWindowDetector()

    if sys.platform.startswith("linux"):

        try:
            return LinuxWindowDetector()

        except Exception:
            return NullWindowDetector()

    return NullWindowDetector()
