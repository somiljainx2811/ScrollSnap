"""
ScrollSnap
==========

Activity Logger Plugin

A minimal example plugin: logs capture/stitch/export activity
through the standard logger, purely by listening on the event
bus. Demonstrates that plugins never need to touch controllers
or core internals directly.
"""

from __future__ import annotations

from plugins.api import Plugin, PluginContext
from utils.logger import get_logger


logger = get_logger("plugin.activity_logger")


class ActivityLoggerPlugin(Plugin):

    name = "Activity Logger"

    version = "1.0.0"

    description = "Logs capture, stitch, and export activity."

    def activate(self, context: PluginContext) -> None:

        self._subscribe(context, "capture.started", self._on_capture_started)

        self._subscribe(context, "stitch.completed", self._on_stitch_completed)

        self._subscribe(context, "export.completed", self._on_export_completed)

    def _on_capture_started(self, event) -> None:
        logger.info("Capture started.")

    def _on_stitch_completed(self, event) -> None:

        result = event.data

        if result is not None and getattr(result, "success", False):

            logger.info(
                "Stitched %d frame(s) -> %dx%d",
                result.frame_count, result.width, result.height,
            )

        else:
            logger.warning("Stitch failed: %s", getattr(result, "error", ""))

    def _on_export_completed(self, event) -> None:
        logger.info("Exported to %s", event.data)
