"""
Mock-based verification of the Windows-only code paths
(`platforms.window_detector.WindowsWindowDetector` and
`platforms.dpi.enable_dpi_awareness`'s Windows branch).

IMPORTANT HONESTY NOTE: these tests verify that the *code*
correctly calls the documented Win32 ctypes API with the right
argument shapes and handles return values sensibly - they run on
any OS by injecting a fake `ctypes.windll`. They do **not** prove
the code behaves correctly against a real Windows OS, since
`ctypes.windll` does not exist on non-Windows platforms at all.
Treat these as "the logic doesn't have silly bugs", not as
"verified on Windows".
"""

from __future__ import annotations

import ctypes
import sys
import types
from unittest.mock import MagicMock

import pytest

from platforms import dpi, window_detector


@pytest.fixture
def fake_windll(monkeypatch):
    """
    Inject a fake `ctypes.windll` (which doesn't exist on
    non-Windows platforms) so Windows-only code can be exercised
    anywhere. Also stands in `WINFUNCTYPE` (stdcall-only, also
    Windows-only) with the cross-platform `CFUNCTYPE` - fine for
    exercising the surrounding Python logic, since the calling
    convention itself isn't what these tests are checking.
    """

    fake = types.SimpleNamespace(
        user32=MagicMock(),
        kernel32=MagicMock(),
    )

    monkeypatch.setattr(ctypes, "windll", fake, raising=False)

    if not hasattr(ctypes, "WINFUNCTYPE"):
        monkeypatch.setattr(
            ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE, raising=False
        )

    return fake


class TestWindowsWindowDetector:

    def test_construction_binds_user32_and_kernel32(self, fake_windll):

        detector = window_detector.WindowsWindowDetector()

        assert detector._user32 is fake_windll.user32

        assert detector._kernel32 is fake_windll.kernel32

    def test_active_window_calls_get_foreground_window(self, fake_windll):

        fake_windll.user32.GetForegroundWindow.return_value = 12345

        fake_windll.user32.GetWindowTextLengthW.return_value = 5

        fake_windll.user32.IsWindowVisible.return_value = 1

        fake_windll.user32.IsIconic.return_value = 0

        fake_windll.user32.IsZoomed.return_value = 0

        fake_windll.user32.GetWindowThreadProcessId.side_effect = (
            lambda handle, pid_ref: setattr(pid_ref._obj, "value", 999)
        )

        fake_windll.kernel32.OpenProcess.return_value = 0  # no access, ok

        detector = window_detector.WindowsWindowDetector()

        info = detector.active_window()

        fake_windll.user32.GetForegroundWindow.assert_called_once()

        assert info is not None

        assert info.handle == 12345

        assert info.process_id == 999

    def test_enumerate_windows_filters_invisible(self, fake_windll):

        def fake_enum_windows(callback, _lparam):

            callback(1, 0)

            callback(2, 0)

            return True

        fake_windll.user32.EnumWindows.side_effect = fake_enum_windows

        fake_windll.user32.IsWindowVisible.side_effect = lambda h: h == 1

        fake_windll.user32.GetWindowTextLengthW.return_value = 0

        fake_windll.user32.IsIconic.return_value = 0

        fake_windll.user32.IsZoomed.return_value = 0

        fake_windll.user32.GetWindowThreadProcessId.side_effect = (
            lambda handle, pid_ref: setattr(pid_ref._obj, "value", 0)
        )

        fake_windll.kernel32.OpenProcess.return_value = 0

        detector = window_detector.WindowsWindowDetector()

        windows = detector.enumerate_windows()

        assert len(windows) == 1

        assert windows[0].handle == 1

    def test_window_from_handle_returns_none_for_zero(self, fake_windll):

        detector = window_detector.WindowsWindowDetector()

        assert detector.window_from_handle(0) is None


class TestFactoryFallsBackSafely:

    def test_create_window_detector_falls_back_when_construction_fails(
        self, monkeypatch
    ):

        monkeypatch.setattr(sys, "platform", "win32")

        monkeypatch.setattr(
            window_detector,
            "WindowsWindowDetector",
            MagicMock(side_effect=RuntimeError("no win32 available here")),
        )

        detector = window_detector.create_window_detector()

        assert isinstance(detector, window_detector.NullWindowDetector)


class TestDpiAwareness:

    def test_noop_true_on_non_windows(self, monkeypatch):

        monkeypatch.setattr(sys, "platform", "linux")

        assert dpi.enable_dpi_awareness() is True

    def test_uses_modern_api_when_available(self, monkeypatch, fake_windll):

        monkeypatch.setattr(sys, "platform", "win32")

        fake_windll.user32.SetProcessDpiAwarenessContext.return_value = 1

        assert dpi.enable_dpi_awareness() is True

        fake_windll.user32.SetProcessDpiAwarenessContext.assert_called_once()

    def test_falls_back_to_shcore_api(self, monkeypatch, fake_windll):

        monkeypatch.setattr(sys, "platform", "win32")

        fake_windll.user32.SetProcessDpiAwarenessContext.side_effect = (
            AttributeError
        )

        fake_windll.shcore = MagicMock()

        fake_windll.shcore.SetProcessDpiAwareness.return_value = 0

        assert dpi.enable_dpi_awareness() is True

    def test_falls_back_to_legacy_api(self, monkeypatch, fake_windll):

        monkeypatch.setattr(sys, "platform", "win32")

        fake_windll.user32.SetProcessDpiAwarenessContext.side_effect = (
            AttributeError
        )

        fake_windll.shcore = MagicMock()

        fake_windll.shcore.SetProcessDpiAwareness.side_effect = AttributeError

        fake_windll.user32.SetProcessDPIAware.return_value = 1

        assert dpi.enable_dpi_awareness() is True

    def test_returns_false_if_every_api_fails(self, monkeypatch, fake_windll):

        monkeypatch.setattr(sys, "platform", "win32")

        fake_windll.user32.SetProcessDpiAwarenessContext.side_effect = (
            AttributeError
        )

        fake_windll.shcore = MagicMock()

        fake_windll.shcore.SetProcessDpiAwareness.side_effect = AttributeError

        fake_windll.user32.SetProcessDPIAware.side_effect = AttributeError

        assert dpi.enable_dpi_awareness() is False
