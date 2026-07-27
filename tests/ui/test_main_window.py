"""
Live tests for ui.main_window.MainWindow: region selection,
single snapshots, scrolling capture, and the history/recovery/
plugin wiring around them. Requires a real or virtual display.
"""

from __future__ import annotations

import time

from tests.conftest import requires_display


@requires_display
class TestMainWindow:

    def test_launches_with_expected_widgets(self, monkeypatch, tmp_path):

        _isolate_storage(monkeypatch, tmp_path)

        from ui.main_window import MainWindow

        window = MainWindow()

        window.update()

        try:

            assert window.title().startswith("ScrollSnap")

            assert len(window.winfo_children()) > 0

            assert len(window.plugin_loader.active_plugins) >= 3

        finally:
            window.destroy()

    def test_region_selection_updates_label(self, monkeypatch, tmp_path):

        _isolate_storage(monkeypatch, tmp_path)

        from ui.main_window import MainWindow

        window = MainWindow()

        window.update()

        try:

            window._on_region_selected(0, 0, 300, 200)

            assert "300" in window.region_label.cget("text")

        finally:
            window.destroy()

    def test_snap_opens_preview_and_records_history(
        self, monkeypatch, tmp_path
    ):

        _isolate_storage(monkeypatch, tmp_path)

        from ui.main_window import MainWindow

        window = MainWindow()

        window.update()

        try:

            window._on_region_selected(0, 0, 200, 150)

            window._snap()

            window.update()

            assert len(window._preview_windows) == 1

            assert len(window.history_controller.recent_entries()) == 1

        finally:
            window.destroy()

    def test_scrolling_capture_stitches_and_opens_preview(
        self, monkeypatch, tmp_path
    ):

        _isolate_storage(monkeypatch, tmp_path)

        from ui.main_window import MainWindow

        window = MainWindow()

        window.update()

        try:

            window._on_region_selected(0, 0, 200, 150)

            window.interval_var.set(0.2)

            window._start_capture()

            assert window._is_capturing is True

            time.sleep(0.9)

            window._stop_capture()

            window.update()

            assert window._is_capturing is False

            assert "Stitched" in window.status_var.get() or (
                "1 frame" in window.status_var.get()
            )

        finally:
            window.destroy()

    def test_crash_then_restart_offers_recovery(self, monkeypatch, tmp_path):

        _isolate_storage(monkeypatch, tmp_path)

        from ui.main_window import MainWindow

        window = MainWindow()

        window.update()

        window._on_region_selected(0, 0, 200, 150)

        window.interval_var.set(0.2)

        window._start_capture()

        time.sleep(0.5)

        # Simulate a crash: stop the background thread but skip the
        # normal _stop_capture()/end_session() cleanup entirely.
        window.capture_controller.stop_capture()

        window.destroy()

        from ui.main_window import MainWindow as MainWindow2

        window2 = MainWindow2()

        window2.update()

        try:
            assert window2.history_controller.has_pending_recovery()

        finally:
            window2.history_controller.discard_recovery()

            window2.destroy()


def _isolate_storage(monkeypatch, tmp_path) -> None:
    """
    Point every storage location at a throwaway temp directory so
    tests don't read/write the real project's history/cache/
    session files.
    """

    from history import recovery
    from storage import cache, recent_projects, thumbnails

    monkeypatch.setattr(cache, "DEFAULT_CACHE_DIR", tmp_path / "cache")

    monkeypatch.setattr(
        thumbnails, "DEFAULT_THUMBNAIL_DIR", tmp_path / "thumbnails"
    )

    monkeypatch.setattr(
        recent_projects, "DEFAULT_INDEX_PATH", tmp_path / "recent.json"
    )

    monkeypatch.setattr(
        recovery, "DEFAULT_SESSION_DIR", tmp_path / "sessions"
    )
