"""
ScrollSnap
==========

Content-Based Vertical Alignment

Real image-comparison logic for answering the two questions the
project previously answered with placeholders:

    "How far did the page actually scroll between these two
     frames?" (used by auto-scroll end detection)

    "How many pixels of Frame A are repeated in Frame B?"
     (used by stitching, to place frames correctly)

Both questions are really the same underlying problem: find the
vertical shift that best aligns two images. This module solves
it once, with a lightweight 1D row-signature cross-correlation
(no numpy/OpenCV dependency), and both
`image_processing.pillow_backend.PillowOverlapDetector` and
`PillowScrollDetector` are thin wrappers around it.

Algorithm
---------
1. Reduce each image to a "row signature": one brightness value
   per row, computed by resizing to width=1 with box filtering
   (a fast, C-level way to get a per-row average without a
   manual pixel loop).
2. For each candidate shift `s` (how many of `previous`'s rows
   have scrolled off the top), compare `previous`'s rows
   `[s : s+L]` against `current`'s rows `[0 : L]` using mean
   absolute difference.
3. Pick the shift with the lowest difference, and derive a
   confidence score from how much better that shift is than the
   "nothing moved" (shift=0) baseline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PIL import Image


@dataclass(slots=True)
class VerticalAlignmentResult:
    """
    Best-guess vertical alignment between two frames.
    """

    shift: int
    """Rows of `previous` that have scrolled off the top."""

    overlap_rows: int
    """How many rows of overlap that implies."""

    error: float
    """Mean absolute brightness difference at the chosen shift (0-255)."""

    confidence: float
    """0.0-1.0: how much better `shift` is than assuming no movement."""

    moved: bool


def _row_signature(image: Any, height: int) -> list[int]:
    """
    Collapse `image` to one brightness value per row.
    """

    grayscale = image.convert("L")

    reduced = grayscale.resize((1, height), Image.BOX)

    return list(reduced.getdata())


def quick_fingerprint(image: Any, size: int = 32) -> bytes:
    """
    A small, fast "does this look the same" fingerprint - a
    downsampled grayscale thumbnail's raw bytes. Cheap enough to
    compute several times a second while waiting for a page to
    finish rendering after a scroll (see
    `capture.auto_scroll.smart_timing.StabilityWaiter`), unlike
    the full row-signature search `estimate_vertical_alignment`
    does (which is precise about *how much* moved, not just
    *whether* anything changed).
    """

    return image.convert("L").resize((size, size), Image.BOX).tobytes()


def images_visually_stable(
    fingerprint_a: bytes,
    fingerprint_b: bytes,
    tolerance: float = 3.0,
) -> bool:
    """
    True if two fingerprints (from `quick_fingerprint`) are close
    enough to call "the same picture" - i.e. rendering/animation
    has settled between two quick probes.
    """

    if len(fingerprint_a) != len(fingerprint_b) or not fingerprint_a:
        return False

    diff = sum(
        abs(a - b) for a, b in zip(fingerprint_a, fingerprint_b)
    ) / len(fingerprint_a)

    return diff <= tolerance


def estimate_vertical_alignment(
    previous_image: Any,
    current_image: Any,
    min_overlap_ratio: float = 0.10,
    max_overlap_ratio: float = 0.90,
    movement_threshold: float = 3.0,
) -> VerticalAlignmentResult:
    """
    Estimate how far `current_image` has scrolled relative to
    `previous_image`, assuming both are screenshots of the same
    vertically-scrollable region.

    Known limitation: like any simple correlation-based matcher,
    this can be fooled by highly periodic/repetitive content
    (e.g. a long list of near-identical rows) where several
    different shifts match almost equally well. The ambiguity
    check below detects that situation and reports a low
    confidence rather than confidently returning a
    possibly-wrong shift, but it cannot fully resolve the
    ambiguity - genuinely repetitive pages remain the hard case
    for this technique (and for most naive scroll-stitchers).
    """

    prev_height = previous_image.height

    curr_height = current_image.height

    height = min(prev_height, curr_height)

    if height < 4:

        return VerticalAlignmentResult(
            shift=0, overlap_rows=0, error=0.0,
            confidence=0.0, moved=False,
        )

    previous_rows = _row_signature(previous_image, prev_height)

    current_rows = _row_signature(current_image, curr_height)

    if _is_low_variance(previous_rows) or _is_low_variance(current_rows):

        # Near-blank/loading content: any "match" would be
        # coincidental, not meaningful.
        return VerticalAlignmentResult(
            shift=0, overlap_rows=height, error=0.0,
            confidence=0.0, moved=False,
        )

    min_shift = max(1, int(height * (1 - max_overlap_ratio)))

    max_shift = max(
        min_shift, int(height * (1 - min_overlap_ratio))
    )

    max_shift = min(max_shift, height - 1)

    baseline_error = _mean_abs_diff(
        previous_rows[:height], current_rows[:height]
    )

    errors: dict[int, float] = {}

    for shift in range(min_shift, max_shift + 1):

        overlap_len = min(prev_height - shift, curr_height)

        if overlap_len <= 0:
            continue

        errors[shift] = _mean_abs_diff(
            previous_rows[shift:shift + overlap_len],
            current_rows[:overlap_len],
        )

    if not errors:

        return VerticalAlignmentResult(
            shift=0, overlap_rows=height, error=baseline_error,
            confidence=0.0, moved=False,
        )

    best_shift = min(errors, key=errors.get)

    best_error = errors[best_shift]

    moved = (
        best_shift > 0
        and (baseline_error - best_error) > movement_threshold
    )

    if not moved:

        return VerticalAlignmentResult(
            shift=0,
            overlap_rows=height,
            error=baseline_error,
            confidence=_confidence(baseline_error, baseline_error),
            moved=False,
        )

    confidence = _confidence(best_error, baseline_error)

    confidence *= _ambiguity_penalty(errors, best_shift, best_error, height)

    overlap_rows = min(prev_height - best_shift, curr_height)

    return VerticalAlignmentResult(
        shift=best_shift,
        overlap_rows=overlap_rows,
        error=best_error,
        confidence=confidence,
        moved=True,
    )


def _is_low_variance(rows: list[int], threshold: float = 3.0) -> bool:
    """
    True if `rows` has almost no brightness variation - a blank,
    loading, or solid-color frame, where "alignment" is
    meaningless.
    """

    if len(rows) < 2:
        return True

    mean = sum(rows) / len(rows)

    variance = sum((v - mean) ** 2 for v in rows) / len(rows)

    return variance ** 0.5 < threshold


def _ambiguity_penalty(
    errors: dict[int, float],
    best_shift: int,
    best_error: float,
    height: int,
) -> float:
    """
    Detects periodic/repetitive content: if some other candidate
    shift, far enough away from `best_shift` to be a genuinely
    different alignment, scores almost as well, the match is
    ambiguous and the caller should trust it less. Returns a
    multiplier in (0, 1] to scale confidence down accordingly.
    """

    far_enough = max(4, int(height * 0.05))

    runner_up = min(
        (
            error for shift, error in errors.items()
            if abs(shift - best_shift) >= far_enough
        ),
        default=None,
    )

    if runner_up is None:
        return 1.0

    if runner_up <= 0:
        return 1.0

    # How close the runner-up is to the best match, as a fraction
    # (0 = identical scores -> fully ambiguous, 1+ = clearly worse).
    separation = (runner_up - best_error) / runner_up

    return max(0.15, min(1.0, separation * 2))


def _mean_abs_diff(a: list[int], b: list[int]) -> float:

    if not a or not b:
        return 255.0

    length = min(len(a), len(b))

    return sum(abs(a[i] - b[i]) for i in range(length)) / length


def _confidence(best_error: float, baseline_error: float) -> float:
    """
    0.0-1.0 confidence: how much better the chosen alignment is
    than assuming nothing moved, normalized so a perfect match
    (error=0) with a poor baseline gives high confidence, and a
    match barely better than baseline gives low confidence.
    """

    if baseline_error <= 0:
        return 0.5

    improvement = (baseline_error - best_error) / baseline_error

    return max(0.0, min(1.0, improvement))
