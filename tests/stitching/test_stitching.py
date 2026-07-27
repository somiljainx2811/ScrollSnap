"""
Tests for the real (Pillow-backed) stitching pipeline:
blending, crop optimization, seam optimization, and export.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from image_processing.pillow_backend import (
    PillowAlphaBlender,
    PillowCropOptimizer,
    PillowMaskBackend,
    PillowSeamOptimizer,
    write_export,
)
from models.frame import Frame
from models.rectangle import Rectangle
from stitching.alignment import AlignmentEngine
from stitching.duplicate_removal import DuplicateRemover
from stitching.exporters import ExportFormat, StitchExporter
from stitching.overlap_detector import SimpleOverlapDetector
from stitching.stitch_engine import StitchEngine


def make_frame(color, sequence, size=(300, 200)):

    image = Image.new("RGB", size, color)

    draw = ImageDraw.Draw(image)

    draw.text((10, 10), f"frame {sequence}", fill=(255, 255, 255))

    return Frame(
        image=image,
        region=Rectangle.from_xywh(0, 0, size[0], size[1]),
        sequence=sequence,
    )


def build_engine():

    return StitchEngine(
        overlap_detector=SimpleOverlapDetector(),
        alignment_engine=AlignmentEngine(),
        duplicate_remover=DuplicateRemover(),
        blender=PillowAlphaBlender(),
        crop_optimizer=PillowCropOptimizer(),
    )


class TestFrameRegionBugfix:
    """
    Regression test for the bug where captured frames never had
    their `region` set, silently zeroing Frame.width/height and
    breaking overlap detection / canvas sizing.
    """

    def test_frame_width_height_match_region(self):

        frame = make_frame((10, 10, 10), 0, size=(400, 300))

        assert frame.width == 400

        assert frame.height == 300

    def test_frame_without_region_has_zero_dimensions(self):

        image = Image.new("RGB", (400, 300))

        frame = Frame(image=image)  # region intentionally omitted

        assert frame.width == 0

        assert frame.height == 0


class TestStitchEngine:

    def test_stitch_multiple_frames_succeeds(self):

        frames = [
            make_frame((200, 30, 30), 0),
            make_frame((30, 200, 30), 1),
            make_frame((30, 30, 200), 2),
        ]

        result = build_engine().stitch(frames)

        assert result.success, result.error

        assert result.width > 0

        assert result.height > frames[0].height  # taller than one frame

        assert isinstance(result.image, Image.Image)

    def test_stitch_single_frame(self):

        frames = [make_frame((100, 100, 100), 0)]

        result = build_engine().stitch(frames)

        assert result.success

        assert result.frame_count == 1

    def test_stitch_empty_list_fails_gracefully(self):

        result = build_engine().stitch([])

        assert not result.success

    def test_second_stitch_on_same_engine_does_not_reuse_stale_index(self):
        """
        Regression test: `StitchEngine` is long-lived (constructed
        once per app session by `StitchController`), but
        `AlignmentEngine` keeps a running `frame_index` across
        calls to `calculate()`. Without an explicit reset at the
        start of each stitch, a second (especially shorter)
        capture session in the same app run would carry over the
        first stitch's frame_index, overrun the new frame list,
        and blow up with "list index out of range".
        """

        engine = build_engine()

        first_frames = [
            make_frame((200, 30, 30), 0),
            make_frame((30, 200, 30), 1),
            make_frame((30, 30, 200), 2),
            make_frame((10, 10, 10), 3),
            make_frame((20, 20, 20), 4),
        ]

        first_result = engine.stitch(first_frames)

        assert first_result.success, first_result.error

        second_frames = [
            make_frame((240, 240, 30), 0),
            make_frame((30, 240, 240), 1),
        ]

        second_result = engine.stitch(second_frames)

        assert second_result.success, second_result.error

        assert second_result.frame_count == 2


class TestSeamOptimizer:

    def test_optimize_returns_same_size_image(self):

        frames = [
            make_frame((200, 30, 30), 0),
            make_frame((30, 200, 30), 1),
        ]

        stitched = build_engine().stitch(frames)

        seam_result = PillowSeamOptimizer().optimize(stitched.image)

        assert seam_result.image.size == stitched.image.size


class TestExport:

    def test_write_png(self, tmp_path):

        image = Image.new("RGB", (50, 50), (1, 2, 3))

        exporter = StitchExporter()

        prepared = exporter.prepare(
            image, str(tmp_path / "out"), ExportFormat.PNG
        )

        assert prepared.success

        path = write_export(prepared.request)

        assert path.exists()

        assert path.suffix == ".png"

    def test_write_jpeg_flattens_alpha(self, tmp_path):

        image = Image.new("RGBA", (50, 50), (1, 2, 3, 128))

        exporter = StitchExporter()

        prepared = exporter.prepare(
            image, str(tmp_path / "out"), ExportFormat.JPEG, quality=80
        )

        path = write_export(prepared.request)

        assert path.exists()

        reopened = Image.open(path)

        assert reopened.mode == "RGB"  # JPEG has no alpha channel


class TestEndToEndShapeCutout:

    def test_stitch_then_mask(self):

        from shapes.circle import CircleShape
        from shapes.mask_renderer import MaskRenderer

        frames = [
            make_frame((200, 30, 30), 0),
            make_frame((30, 200, 30), 1),
        ]

        stitched = build_engine().stitch(frames)

        renderer = MaskRenderer(backend=PillowMaskBackend())

        shape = CircleShape(0, 0, min(stitched.width, stitched.height) / 2)

        mask_result = renderer.render(shape, stitched.width, stitched.height)

        cutout = renderer.backend.apply(stitched.image, mask_result.mask)

        assert cutout.mode == "RGBA"
