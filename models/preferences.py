"""
ScrollSnap
==========

Preferences Model

Represents all user-configurable application settings.

This model is storage-agnostic and can be serialized to any
persistence backend.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from models.enums import Theme, ExportFormat


@dataclass(slots=True)
class Preferences:
    """
    Application preferences.
    """

    # ---------------------------------------------------------
    # Appearance
    # ---------------------------------------------------------

    theme: Theme = Theme.DARK

    language: str = "en"

    accent_color: str = "#4CAF50"

    animations_enabled: bool = True

    # ---------------------------------------------------------
    # Capture
    # ---------------------------------------------------------

    countdown_seconds: int = 0

    include_cursor: bool = False

    include_window_shadow: bool = False

    auto_copy_clipboard: bool = True

    play_capture_sound: bool = False

    show_selection_magnifier: bool = True

    default_auto_scroll: bool = False

    # ---------------------------------------------------------
    # Export
    # ---------------------------------------------------------

    default_export_format: ExportFormat = ExportFormat.PNG

    default_quality: int = 95

    default_dpi: int = 300

    default_output_directory: str = ""

    overwrite_existing_files: bool = False

    open_after_export: bool = False

    # ---------------------------------------------------------
    # Preview
    # ---------------------------------------------------------

    smooth_zoom: bool = True

    show_grid: bool = False

    remember_zoom: bool = True

    checkerboard_background: bool = True

    # ---------------------------------------------------------
    # History
    # ---------------------------------------------------------

    max_recent_projects: int = 10

    max_history_entries: int = 100

    auto_save: bool = True

    auto_save_interval_seconds: int = 60

    # ---------------------------------------------------------
    # Performance
    # ---------------------------------------------------------

    use_hardware_acceleration: bool = True

    thumbnail_cache_size: int = 512

    max_memory_mb: int = 2048

    worker_threads: int = 4

    # ---------------------------------------------------------
    # Advanced
    # ---------------------------------------------------------

    developer_mode: bool = False

    enable_plugins: bool = True

    check_updates_on_startup: bool = True

    telemetry_enabled: bool = False

    # ---------------------------------------------------------
    # Extension
    # ---------------------------------------------------------

    custom: dict[str, object] = field(default_factory=dict)

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def __post_init__(self) -> None:

        if self.countdown_seconds < 0:
            raise ValueError(
                "countdown_seconds cannot be negative."
            )

        if not (1 <= self.default_quality <= 100):
            raise ValueError(
                "default_quality must be between 1 and 100."
            )

        if self.default_dpi <= 0:
            raise ValueError(
                "default_dpi must be positive."
            )

        if self.max_recent_projects < 0:
            raise ValueError(
                "max_recent_projects cannot be negative."
            )

        if self.max_history_entries < 0:
            raise ValueError(
                "max_history_entries cannot be negative."
            )

        if self.auto_save_interval_seconds <= 0:
            raise ValueError(
                "auto_save_interval_seconds must be positive."
            )

        if self.thumbnail_cache_size <= 0:
            raise ValueError(
                "thumbnail_cache_size must be positive."
            )

        if self.max_memory_mb <= 0:
            raise ValueError(
                "max_memory_mb must be positive."
            )

        if self.worker_threads <= 0:
            raise ValueError(
                "worker_threads must be positive."
            )

    # ---------------------------------------------------------
    # Serialization
    # ---------------------------------------------------------

    def to_dict(self) -> dict[str, object]:
        data = self.__dict__.copy()

        data["theme"] = self.theme.name
        data["default_export_format"] = (
            self.default_export_format.name
        )

        return data

    @classmethod
    def from_dict(
        cls,
        data: dict[str, object],
    ) -> "Preferences":

        values = dict(data)

        values["theme"] = Theme[
            str(values.get("theme", "DARK"))
        ]

        values["default_export_format"] = ExportFormat[
            str(
                values.get(
                    "default_export_format",
                    "PNG",
                )
            )
        ]

        return cls(**values)

    # ---------------------------------------------------------
    # Convenience
    # ---------------------------------------------------------

    def copy(self) -> "Preferences":
        return Preferences.from_dict(
            self.to_dict()
        )

    def __repr__(self) -> str:
        return (
            "Preferences("
            f"theme={self.theme.name}, "
            f"language={self.language!r}, "
            f"format={self.default_export_format.name}"
            ")"
        )