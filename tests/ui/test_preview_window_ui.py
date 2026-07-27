"""
Live tests for ui.preview_window.PreviewWindowUI. Requires a
real or virtual (Xvfb) display.
"""

from __future__ import annotations

from tests.conftest import requires_display


@requires_display
class TestPreviewWindowUI:

    def _make_preview(self, tk_root, image):

        from controllers.preview_controller import PreviewController
        from ui.preview_window import PreviewWindowUI

        controller = PreviewController()

        controller.open(image)

        preview = PreviewWindowUI(tk_root, controller)

        preview.update()

        return preview

    def test_opens_without_error(self, tk_root, solid_image):

        preview = self._make_preview(tk_root, solid_image(500, 400))

        assert preview.controller.window.is_open

    def test_rotate_updates_canvas(self, tk_root, solid_image):

        preview = self._make_preview(tk_root, solid_image(500, 400))

        preview._rotate_cw()

        preview.update()

        # 500x400 rotated 90 -> 400x500
        assert preview.canvas.winfo_width() > 0

    def test_annotation_add_and_undo(self, tk_root, solid_image):

        preview = self._make_preview(tk_root, solid_image(500, 400))

        preview._active_tool = "Rectangle"

        preview._add_annotation((10, 10), (100, 80))

        preview.update()

        assert preview.controller.window.annotations.count == 1

        preview._undo()

        preview.update()

        assert preview.controller.window.annotations.count == 0

    def test_shape_cutout_applies(self, tk_root, solid_image):

        preview = self._make_preview(tk_root, solid_image(400, 400))

        preview._shape_var.set("Circle")

        preview._apply_shape_cutout()

        preview.update()

        assert preview._last_cutout.mode == "RGBA"

    def test_close_invokes_callback(self, tk_root, solid_image):

        closed = {"value": False}

        from controllers.preview_controller import PreviewController
        from ui.preview_window import PreviewWindowUI

        controller = PreviewController()

        controller.open(solid_image(100, 100))

        preview = PreviewWindowUI(
            tk_root, controller, on_close=lambda: closed.update(value=True)
        )

        preview.update()

        preview._on_close()

        assert closed["value"] is True
