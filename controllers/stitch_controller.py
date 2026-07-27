"""
ScrollSnap
==========

Stitch Controller

The UI-facing entry point for turning a list of captured frames
into one final image, using the real Pillow-backed stitching
pipeline.
"""

from __future__ import annotations

from models.frame import Frame

from stitching.alignment import AlignmentEngine
from stitching.stitch_engine import StitchEngine, StitchResult

from image_processing.pillow_backend import (
    PillowAlphaBlender,
    PillowCropOptimizer,
    PillowDuplicateRemover,
    PillowOverlapDetector,
    PillowSeamOptimizer,
)

from core.event_bus import EventBus, event_bus as default_event_bus


class StitchController:
    """
    Coordinates stitching a capture session's frames into a
    single image.
    """

    def __init__(self, bus: EventBus | None = None) -> None:

        self._bus = bus or default_event_bus

        self._engine = StitchEngine(
            overlap_detector=PillowOverlapDetector(),
            alignment_engine=AlignmentEngine(),
            duplicate_remover=PillowDuplicateRemover(),
            blender=PillowAlphaBlender(),
            crop_optimizer=PillowCropOptimizer(),
        )

        self._seam_optimizer = PillowSeamOptimizer()

        self._last_result: StitchResult | None = None

    @property
    def last_result(self) -> StitchResult | None:
        return self._last_result

    def stitch(
        self,
        frames: list[Frame],
        smooth_seams: bool = True,
    ) -> StitchResult:

        self._bus.publish("stitch.started", {"frames": len(frames)})

        result = self._engine.stitch(frames)

        if result.success and smooth_seams:

            seam_result = self._seam_optimizer.optimize(result.image)

            result = StitchResult(
                image=seam_result.image,
                frame_count=result.frame_count,
                width=getattr(seam_result.image, "width", result.width),
                height=getattr(
                    seam_result.image, "height", result.height
                ),
                success=True,
            )

        self._last_result = result

        self._bus.publish("stitch.completed", result)

        return result
