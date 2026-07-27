"""
ScrollSnap
==========

Export Controller

The UI-facing entry point for writing a final image to disk in
any supported format.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.event_bus import EventBus, event_bus as default_event_bus
from image_processing.pillow_backend import write_export
from stitching.exporters import ExportFormat, StitchExporter


_EXTENSION_FORMATS = {
    ".png": ExportFormat.PNG,
    ".jpg": ExportFormat.JPEG,
    ".jpeg": ExportFormat.JPEG,
    ".webp": ExportFormat.WEBP,
    ".tif": ExportFormat.TIFF,
    ".tiff": ExportFormat.TIFF,
    ".pdf": ExportFormat.PDF,
}


class ExportController:
    """
    Coordinates writing a finished image to disk.
    """

    def __init__(self, bus: EventBus | None = None) -> None:

        self._bus = bus or default_event_bus

        self._exporter = StitchExporter()

    def format_for_path(self, path: str | Path) -> ExportFormat:

        suffix = Path(path).suffix.lower()

        return _EXTENSION_FORMATS.get(suffix, ExportFormat.PNG)

    def export(
        self,
        image: Any,
        path: str | Path,
        format: ExportFormat | None = None,
        quality: int = 95,
        metadata: dict | None = None,
    ) -> Path:

        export_format = format or self.format_for_path(path)

        result = self._exporter.prepare(
            image=image,
            filename=str(path),
            format=export_format,
            quality=quality,
            metadata=metadata,
        )

        if not result.success:
            self._bus.publish("export.failed", result.error)
            raise RuntimeError(result.error)

        written_path = write_export(result.request)

        self._bus.publish("export.completed", written_path)

        return written_path
