# ScrollSnap Test Suite

## Running

```bash
pip install -r requirements-dev.txt
pytest
```

That runs everything that can run in your environment and skips
the rest with a clear reason (see below).

## What's covered

- **shapes/** - every shape's geometry + real Pillow mask rasterization
- **stitching/** - real blending/crop/seam/export pipeline, including a
  regression test for the `Frame.region` bug (frames silently had
  zero width/height before being fixed)
- **preview/** - editing history (crop/rotate/flip/undo/redo),
  annotations (add/remove/hit-test/undo), and the `PreviewWindow`
  state machine
- **models/** - `Rectangle` geometry + a regression test for the
  missing `to_dict`/`from_dict` methods that `Frame` and
  `CaptureRegion` depended on but didn't exist
- **history/** - crash recovery (cache a frame, "crash", restart,
  confirm it's recoverable) and capture history storage
- **plugins/** - discovery, activation via the event bus,
  notification/clipboard behavior, and teardown
- **ocr/** - text extraction, Markdown export, searchable PDF export
- **platforms/** - live tests against the real `mss`/`pynput`/Linux
  window-detector backends, *plus* mock-based tests for the
  Windows-only ctypes code paths (window detector, DPI awareness)
- **ui/** - the selection overlay (drag, live magnifier, resize
  handles, confirm/cancel), the preview window (rotate/annotate/
  undo/shape-cutout), and the main window (region select -> snap /
  scrolling capture -> history -> crash recovery)
- **integration/** - the full real pipeline end-to-end: screen
  capture -> stitch -> preview/edit/annotate -> shape cutout ->
  file export
- **capture/test_smart_timing.py, test_capture_scheduler.py** -
  the new adaptive capture-timing feature, and a threading
  regression test it exposed (see below)

## Bugs found and fixed during review (each has a named
regression test so it can't silently come back)

1. `stitching.overlap_detector.SimpleOverlapDetector` always
   assumed a flat 50% overlap between frames, regardless of the
   actual scroll distance - stitched output was often visibly
   misaligned. Replaced with `PillowOverlapDetector`, a real
   content-based match (`image_processing/alignment.py`).
2. `capture.auto_scroll.scroll_detector.ScrollDetector.
   _estimate_offset()` was hardcoded to always return `10`, so
   auto-scroll's "stop automatically at the end of the page"
   never actually worked - it always believed the page had just
   moved. Replaced with `PillowScrollDetector`, using the same
   real alignment algorithm.
3. `stitching.duplicate_removal.DuplicateRemover.remove()` never
   removed a single frame, regardless of what `detect()` found -
   the name was aspirational. Replaced with
   `PillowDuplicateRemover`, which genuinely drops near-identical
   consecutive frames.
4. `stitching.blending.AlphaBlender._calculate_canvas_size()`
   completely ignored the first frame (`zip(frames, alignments)`
   silently drops it, since `alignments` only covers transitions
   *between* frames). This was always broken but never observed
   until fix #3 started legitimately collapsing sessions down to
   a single frame, producing a 0x0 canvas. Fixed to seed the
   canvas size with the first frame's own dimensions.
5. A threading bug in `capture.capture_scheduler.CaptureScheduler.
   stop()`: calling it from *within* its own callback (which
   becomes a real code path once fix #2 lets end-detection
   actually trigger a self-stop) tried to `Thread.join()` the
   currently-running thread, raising `RuntimeError`. Fixed by
   skipping the blocking join when called from the scheduler's
   own thread.

## New feature: adaptive "smart capture timing"

`capture/auto_scroll/smart_timing.py`'s `StabilityWaiter` polls
the real screen after each scroll and captures as soon as
rendering visibly settles (or gives up after a timeout),
replacing a fixed delay. This was an explicit item in
ScrollSnap's original roadmap that had never been implemented.
Toggle it via the "Smart timing" checkbox in the main window, or
`CaptureController.start_capture(smart_timing=True)`.


## Honesty notes - what these tests do and don't prove

- Tests tagged `requires_display` need a real or virtual X server
  (`DISPLAY` env var set) - they're auto-skipped otherwise. Use
  Xvfb in CI: `Xvfb :99 -screen 0 1280x800x24 & DISPLAY=:99 pytest`.
- Tests tagged `requires_tesseract` are skipped if the `tesseract`
  binary isn't installed.
- **The Windows-only code (`platforms/window_detector.py`'s
  `WindowsWindowDetector`, `platforms/dpi.py`'s Windows branch) is
  tested by injecting a fake `ctypes.windll`, since the real one
  only exists on Windows.** This verifies the Python logic calls
  the documented Win32 API with sensible arguments and handles
  return values correctly - it does **not** prove the code behaves
  correctly against a real Windows OS. Nothing in this repo has
  been run on actual Windows.
- The `requires_display` tests all ran here against Xvfb (a
  virtual single-monitor X server), not a real multi-monitor setup
  or a real Windows/macOS display. Multi-monitor geometry and
  Windows DPI-scaling behavior are implemented per the documented
  APIs but have only been exercised against a single virtual
  display.
