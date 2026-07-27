"""
Live tests for ui.selection_overlay.SelectionOverlay: the
drag-to-select flow, live magnifier, and draggable resize
handles. Requires a real or virtual (Xvfb) display.
"""

from __future__ import annotations

from tests.conftest import requires_display
from tests.ui.conftest import FakeEvent


@requires_display
class TestSelectionOverlay:

    def _make_overlay(self, tk_root):

        from ui.selection_overlay import SelectionOverlay

        result = {}

        overlay = SelectionOverlay(
            tk_root, lambda *coords: result.update(coords=coords)
        )

        return overlay, result

    def test_starts_idle(self, tk_root):

        overlay, _ = self._make_overlay(tk_root)

        overlay.update()

        assert overlay._mode == "idle"

    def test_drag_shows_magnifier(self, tk_root):

        overlay, _ = self._make_overlay(tk_root)

        overlay.update()

        overlay._on_press(FakeEvent(50, 50))

        overlay._on_drag(FakeEvent(120, 100))

        overlay.update()

        assert overlay._mode == "dragging"

        assert len(overlay.canvas.find_withtag("magnifier")) > 0

    def test_release_enters_adjusting_with_handles(self, tk_root):

        overlay, _ = self._make_overlay(tk_root)

        overlay.update()

        overlay._on_press(FakeEvent(50, 50))

        overlay._on_drag(FakeEvent(300, 250))

        overlay._on_release(FakeEvent(300, 250))

        overlay.update()

        assert overlay._mode == "adjusting"

        assert len(overlay.canvas.find_withtag("handle")) == 8

    def test_too_small_selection_stays_idle(self, tk_root):

        overlay, _ = self._make_overlay(tk_root)

        overlay.update()

        overlay._on_press(FakeEvent(50, 50))

        overlay._on_drag(FakeEvent(55, 55))

        overlay._on_release(FakeEvent(55, 55))

        overlay.update()

        assert overlay._mode == "idle"

    def test_resize_via_handle_changes_rect(self, tk_root):

        overlay, _ = self._make_overlay(tk_root)

        overlay.update()

        overlay._on_press(FakeEvent(50, 50))

        overlay._on_drag(FakeEvent(300, 250))

        overlay._on_release(FakeEvent(300, 250))

        overlay.update()

        se = overlay._handle_positions()["se"]

        overlay._on_press(FakeEvent(int(se[0]), int(se[1])))

        assert overlay._mode == "resizing"

        overlay._on_drag(FakeEvent(400, 350))

        overlay._on_release(FakeEvent(400, 350))

        overlay.update()

        assert overlay._rect[2] == 400

        assert overlay._rect[3] == 350

    def test_confirm_calls_back_with_desktop_coordinates(self, tk_root):

        overlay, result = self._make_overlay(tk_root)

        overlay.update()

        overlay._on_press(FakeEvent(10, 10))

        overlay._on_drag(FakeEvent(200, 150))

        overlay._on_release(FakeEvent(200, 150))

        overlay.update()

        overlay._confirm()

        assert result["coords"] == (10, 10, 200, 150)

    def test_escape_cancels_with_none_coordinates(self, tk_root):

        overlay, result = self._make_overlay(tk_root)

        overlay.update()

        overlay._cancel()

        assert result["coords"] == (None, None, None, None)
