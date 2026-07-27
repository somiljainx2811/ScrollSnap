"""
ScrollSnap
==========

Export Options Model

Represents all configurable export settings.

This model is intentionally independent from the actual export
implementation. Exporters consume this object to determine how
the final image or document should be written.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from models.enums import ExportFormat


@dataclass(frozen=True, slots=True)
class ExportOptions:
    """
    Export configuration.

    Parameters
    ----------
    format
        Output format.

    output_path
        Destination file or directory.

    quality
        JPEG/WebP quality (1-100).

    dpi
        Output DPI.

    optimize
        Enable encoder optimization.

    overwrite
        Allow replacing existing files.

    open_after_export
        Open exported file after completion.

    copy_to_clipboard
        Copy exported image to clipboard.

    include_metadata
        Store metadata if supported.

    searchable_pdf
        Enable OCR searchable PDF generation.

    compression_level
        Compression level (0-9).

    metadata
        Additional exporter-specific options.
    """

    format: ExportFormat = ExportFormat.PNG

    output_path: Path | None = None

    quality: int = 95

    dpi: int = 300

    optimize: bool = True

    overwrite: bool = False

    open_after_export: bool = False

    copy_to_clipboard: bool = False

    include_metadata: bool = True

    searchable_pdf: bool = False

    compression_level: int = 6

    metadata: dict[str, object] = field(default_factory=dict)

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def __post_init__(self) -> None:

        if not (1 <= self.quality <= 100):
            raise ValueError(
                "quality must be between 1 and 100."
            )

        if self.dpi <= 0:
            raise ValueError(
                "dpi must be positive."
            )

        if not (0 <= self.compression_level <= 9):
            raise ValueError(
                "compression_level must be between 0 and 9."
            )

    # ---------------------------------------------------------
    # Convenience
    # ---------------------------------------------------------

    @property
    def is_lossy(self) -> bool:
        return self.format in {
            ExportFormat.JPEG,
            ExportFormat.WEBP,
        }

    @property
    def is_lossless(self) -> bool:
        return not self.is_lossy

    @property
    def requires_quality(self) -> bool:
        return self.is_lossy

    @property
    def is_pdf(self) -> bool:
        return self.format == ExportFormat.PDF

    # ---------------------------------------------------------
    # Serialization
    # ---------------------------------------------------------

    def to_dict(self) -> dict[str, object]:

        return {
            "format": self.format.name,
            "output_path": (
                str(self.output_path)
                if self.output_path
                else None
            ),
            "quality": self.quality,
            "dpi": self.dpi,
            "optimize": self.optimize,
            "overwrite": self.overwrite,
            "open_after_export": self.open_after_export,
            "copy_to_clipboard": self.copy_to_clipboard,
            "include_metadata": self.include_metadata,
            "searchable_pdf": self.searchable_pdf,
            "compression_level": self.compression_level,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, object],
    ) -> "ExportOptions":

        path = data.get("output_path")

        return cls(
            format=ExportFormat[
                str(data.get("format", "PNG"))
            ],
            output_path=(
                Path(path)
                if path
                else None
            ),
            quality=int(data.get("quality", 95)),
            dpi=int(data.get("dpi", 300)),
            optimize=bool(data.get("optimize", True)),
            overwrite=bool(data.get("overwrite", False)),
            open_after_export=bool(
                data.get("open_after_export", False)
            ),
            copy_to_clipboard=bool(
                data.get("copy_to_clipboard", False)
            ),
            include_metadata=bool(
                data.get("include_metadata", True)
            ),
            searchable_pdf=bool(
                data.get("searchable_pdf", False)
            ),
            compression_level=int(
                data.get("compression_level", 6)
            ),
            metadata=dict(
                data.get("metadata", {})
            ),
        )

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def with_output_path(
        self,
        path: Path,
    ) -> "ExportOptions":
        """
        Return a copy with a new output path.
        """

        return ExportOptions(
            format=self.format,
            output_path=path,
            quality=self.quality,
            dpi=self.dpi,
            optimize=self.optimize,
            overwrite=self.overwrite,
            open_after_export=self.open_after_export,
            copy_to_clipboard=self.copy_to_clipboard,
            include_metadata=self.include_metadata,
            searchable_pdf=self.searchable_pdf,
            compression_level=self.compression_level,
            metadata=dict(self.metadata),
        )

    def __repr__(self) -> str:

        return (
            "ExportOptions("
            f"format={self.format.name}, "
            f"path={self.output_path!r}, "
            f"quality={self.quality}, "
            f"dpi={self.dpi}"
            ")"
        )