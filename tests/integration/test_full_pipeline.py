"""
End-to-end integration test covering the full real pipeline:
region selection -> screen capture -> scrolling session ->
stitching -> preview editing/annotation -> shape cutout -> real
file export. Requires a real or virtual display (uses real
`mss`/`pynput` backends, not mocks).
"""

from __future__ import annotations

import time

from tests.conftest import requires_display


@requires_display
class TestFullCapturePipeline:

    def test_single_snap_end_to_end(self, tmp_path):

        from controllers.capture_controller import CaptureController
        from controllers.export_controller import ExportController
        from models.rectangle import Rectangle

        capture = CaptureController()

        try:

            capture.select_region(Rectangle.from_xywh(0, 0, 300, 200))

            frame = capture.snap()

            assert frame.image.size == (300, 200)

            path = ExportController().export(
                frame.image, tmp_path / "snap.png"
            )

            assert path.exists()

        finally:
            capture.shutdown()

    def test_scrolling_capture_stitch_preview_export(self, tmp_path):

        from controllers.capture_controller import CaptureController
        from controllers.export_controller import ExportController
        from controllers.preview_controller import PreviewController
        from controllers.stitch_controller import StitchController
        from models.rectangle import Rectangle
        from shapes.rounded_rectangle import RoundedRectangleShape

        capture = CaptureController()

        try:

            capture.select_region(Rectangle.from_xywh(0, 0, 300, 200))

            capture.start_capture(interval_seconds=0.2, auto_scroll=False)

            time.sleep(0.9)

            capture.stop_capture()

            frames = capture.frames

            assert len(frames) >= 2

            # Regression guard: every frame must carry real
            # dimensions (see the Frame.region bugfix).
            assert all(f.width > 0 and f.height > 0 for f in frames)

            stitch_result = StitchController().stitch(frames)

            assert stitch_result.success

            assert stitch_result.width > 0

            # A genuinely static capture region (nothing is
            # scrolling on this blank Xvfb desktop) now correctly
            # collapses via real duplicate detection, so the
            # result may legitimately be exactly one frame tall
            # rather than taller - both are correct depending on
            # actual on-screen content.
            assert stitch_result.height >= frames[0].height

            preview = PreviewController()

            preview.open(stitch_result.image)

            preview.window.enter_annotating()

            from preview.annotations import Annotation, AnnotationType

            preview.window.annotations.add(
                Annotation(
                    AnnotationType.TEXT, points=[(5, 5)], text="Test"
                )
            )

            preview.window.return_to_viewing()

            final_image = preview.render_for_export()

            assert final_image.size[0] > 0

            cutout = preview.apply_shape_cutout(
                RoundedRectangleShape(
                    0, 0, final_image.width, final_image.height, 20
                )
            )

            assert cutout.mode == "RGBA"

            written = ExportController().export(
                final_image, tmp_path / "final.png"
            )

            assert written.exists()

            assert written.stat().st_size > 0

        finally:
            capture.shutdown()
