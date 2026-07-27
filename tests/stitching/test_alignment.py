"""
Tests for image_processing.alignment (the real content-based
vertical alignment algorithm) and the detector classes built on
top of it: `PillowOverlapDetector`, `PillowScrollDetector`, and
`PillowDuplicateRemover`.

These are regression tests for three real bugs found during
review:

1. `stitching.overlap_detector.SimpleOverlapDetector` always
   assumed a flat 50% overlap regardless of actual scroll
   distance.
2. `capture.auto_scroll.scroll_detector.ScrollDetector.
   _estimate_offset()` was hardcoded to always return `10`,
   so auto-scroll's "stop at the end of the page" never
   actually worked - it always believed movement had occurred.
3. `stitching.duplicate_removal.DuplicateRemover.remove()` never
   removed anything: every frame passed straight through
   regardless of what `detect()` found.
"""

from __future__ import annotations

import random

from PIL import Image, ImageDraw

from image_processing.alignment import estimate_vertical_alignment
from image_processing.pillow_backend import (
    PillowDuplicateRemover,
    PillowOverlapDetector,
    PillowScrollDetector,
)
from models.frame import Frame
from models.rectangle import Rectangle


def make_synthetic_page(width=400, height=4000, seed=1):
    """A non-periodic synthetic 'page' of random-height stripes."""

    random.seed(seed)

    page = Image.new("RGB", (width, height), (255, 255, 255))

    draw = ImageDraw.Draw(page)

    y = 0

    while y < height:

        stripe_height = random.randint(20, 70)

        color = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )

        draw.rectangle([0, y, width, y + stripe_height], fill=color)

        y += stripe_height

    return page


def crop(page, top, size=(400, 300)):
    return page.crop((0, top, size[0], top + size[1]))


class TestEstimateVerticalAlignment:

    def test_recovers_known_shift(self):

        page = make_synthetic_page()

        previous = crop(page, 500)

        current = crop(page, 637)

        result = estimate_vertical_alignment(
            previous, current, min_overlap_ratio=0.0, max_overlap_ratio=0.98
        )

        assert result.moved

        assert abs(result.shift - 137) <= 3

    def test_identical_frames_not_moved(self):

        page = make_synthetic_page()

        frame = crop(page, 100)

        result = estimate_vertical_alignment(frame, frame)

        assert not result.moved

        assert result.shift == 0

    def test_blank_frames_not_moved_and_low_confidence(self):

        blank_a = Image.new("RGB", (300, 400), (255, 255, 255))

        blank_b = Image.new("RGB", (300, 400), (255, 255, 255))

        result = estimate_vertical_alignment(blank_a, blank_b)

        assert not result.moved

        assert result.confidence == 0.0

    def test_large_shift_recovered(self):

        page = make_synthetic_page()

        previous = crop(page, 1000, size=(400, 1200))

        current = crop(page, 1000 + 900, size=(400, 1200))

        result = estimate_vertical_alignment(
            previous, current, min_overlap_ratio=0.0, max_overlap_ratio=0.95
        )

        assert abs(result.shift - 900) <= 5


class TestPillowOverlapDetectorRegression:
    """
    Regression test: the original `SimpleOverlapDetector` always
    returned exactly 50% overlap no matter what actually
    happened on screen.
    """

    def test_overlap_reflects_real_scroll_distance_not_flat_50_percent(self):

        page = make_synthetic_page()

        previous = Frame(
            image=crop(page, 0), region=Rectangle.from_xywh(0, 0, 400, 300)
        )

        # Scrolled by 240px out of a 300px-tall frame (80% shift,
        # 20% overlap) - nowhere near the old hardcoded 50%.
        current = Frame(
            image=crop(page, 240), region=Rectangle.from_xywh(0, 0, 400, 300)
        )

        result = PillowOverlapDetector().detect(previous, current)

        assert result.found

        assert abs(result.offset_y - 240) <= 5

        assert abs(result.overlap_height - 60) <= 5  # NOT 150 (=50%)

    def test_duplicate_frames_flagged_not_found(self):

        page = make_synthetic_page()

        image = crop(page, 0)

        previous = Frame(image=image, region=Rectangle.from_xywh(0, 0, 400, 300))

        current = Frame(image=image, region=Rectangle.from_xywh(0, 0, 400, 300))

        result = PillowOverlapDetector().detect(previous, current)

        assert not result.found

        assert result.confidence == 0.0


class TestPillowScrollDetectorRegression:
    """
    Regression test: `ScrollDetector._estimate_offset()` used to
    always return `10`, so auto-scroll's page-end detection
    never actually triggered on a real stalled/duplicate page.
    """

    def test_real_movement_detected(self):

        page = make_synthetic_page()

        previous = Frame(image=crop(page, 0))

        current = Frame(image=crop(page, 150))

        detector = PillowScrollDetector()

        analysis = detector.analyze(previous, current)

        assert analysis.moved

        assert not analysis.duplicate

        assert abs(analysis.estimated_offset - 150) <= 5

    def test_no_movement_correctly_flagged_as_duplicate(self):

        page = make_synthetic_page()

        image = crop(page, 300)

        previous = Frame(image=image)

        current = Frame(image=image)

        detector = PillowScrollDetector()

        analysis = detector.analyze(previous, current)

        assert not analysis.moved

        assert analysis.duplicate

    def test_end_detector_actually_triggers_on_repeated_stalls(self):

        from capture.auto_scroll.end_detector import EndDetector

        page = make_synthetic_page()

        image = crop(page, 300)  # page has stopped scrolling here

        detector = PillowScrollDetector()

        end_detector = EndDetector(
            duplicate_threshold=3, stall_threshold=3
        )

        previous = Frame(image=image)

        reached_end = False

        for _ in range(5):

            current = Frame(image=image)  # identical: page isn't moving

            analysis = detector.analyze(previous, current)

            end_analysis = end_detector.analyze(analysis)

            if end_analysis.reached_end:
                reached_end = True
                break

            previous = current

        assert reached_end, (
            "End detection never triggered on a genuinely stalled "
            "page - this was the original bug."
        )


class TestPillowDuplicateRemoverRegression:
    """
    Regression test: the original `DuplicateRemover.remove()`
    never removed a single frame regardless of what `detect()`
    found.
    """

    def test_remove_actually_drops_duplicate_frames(self):

        page = make_synthetic_page()

        frames = [
            Frame(image=crop(page, 0), sequence=0),
            Frame(image=crop(page, 180), sequence=1),
            Frame(image=crop(page, 180), sequence=2),  # exact duplicate
            Frame(image=crop(page, 360), sequence=3),
        ]

        remover = PillowDuplicateRemover()

        cleaned = remover.remove(frames)

        assert len(cleaned) == 3  # the duplicate must be gone

    def test_no_duplicates_keeps_all_frames(self):

        page = make_synthetic_page()

        frames = [
            Frame(image=crop(page, 0), sequence=0),
            Frame(image=crop(page, 180), sequence=1),
            Frame(image=crop(page, 360), sequence=2),
        ]

        remover = PillowDuplicateRemover()

        cleaned = remover.remove(frames)

        assert len(cleaned) == 3


class TestCanvasSizeRegression:
    """
    Regression test: `AlphaBlender._calculate_canvas_size()`
    used `zip(frames, alignments)`, but `alignments` only covers
    transitions *between* frames (len(frames)-1 entries), so the
    first frame was always silently ignored. For a single-frame
    list (e.g. after real duplicate removal collapses several
    identical frames down to one) this produced a 0x0 canvas.
    """

    def test_single_frame_produces_nonzero_canvas(self):

        from image_processing.pillow_backend import PillowAlphaBlender

        page = make_synthetic_page()

        frame = Frame(
            image=crop(page, 0), region=Rectangle.from_xywh(0, 0, 400, 300)
        )

        canvas = PillowAlphaBlender().merge([frame], [])

        assert canvas.size == (400, 300)

    def test_stitch_after_duplicate_collapse_has_real_size(self):

        from controllers.stitch_controller import StitchController

        page = make_synthetic_page()

        image = crop(page, 0)

        # Every frame identical -> duplicate remover collapses to 1.
        frames = [
            Frame(image=image, region=Rectangle.from_xywh(0, 0, 400, 300))
            for _ in range(4)
        ]

        result = StitchController().stitch(frames, smooth_seams=False)

        assert result.success

        assert result.frame_count == 1

        assert result.width == 400

        assert result.height == 300


class TestFullPipelineWithRealDetection:
    """
    End-to-end: real overlap detection + real duplicate removal
    together produce a correctly-sized stitched canvas, not the
    old "guess 50% and hope" result.
    """

    def test_stitch_with_injected_duplicates_and_real_scroll_amounts(self):

        from controllers.stitch_controller import StitchController

        page = make_synthetic_page(height=4000, seed=99)

        positions = [0, 180, 360, 540]

        frames = [
            Frame(
                image=crop(page, p),
                region=Rectangle.from_xywh(0, 0, 400, 300),
                sequence=i,
            )
            for i, p in enumerate(positions)
        ]

        # Two extra stalled/duplicate frames at the end.
        frames.append(
            Frame(
                image=crop(page, 540),
                region=Rectangle.from_xywh(0, 0, 400, 300),
                sequence=4,
            )
        )

        frames.append(
            Frame(
                image=crop(page, 540),
                region=Rectangle.from_xywh(0, 0, 400, 300),
                sequence=5,
            )
        )

        result = StitchController().stitch(frames, smooth_seams=False)

        assert result.success

        assert result.frame_count == 4  # duplicates removed

        expected_height = 300 + max(positions)

        assert abs(result.height - expected_height) <= 5
