"""
ScrollSnap Configuration Schema
===============================

Defines all application configuration objects.

This module does NOT read or write files.
Persistence is handled by storage/settings.py.

Rules:
- No UI code.
- No platform-specific code.
- No filesystem operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from version import VERSION_STRING
from constants import (
    DEFAULT_THEME,
    DEFAULT_CAPTURE_FPS,
    DEFAULT_CAPTURE_DELAY,
    DEFAULT_SCROLL_DELAY,
    DEFAULT_SCROLL_STEP,
    DEFAULT_JPEG_QUALITY,
    DEFAULT_PNG_COMPRESSION,
    DEFAULT_CAPTURE_HOTKEY,
    DEFAULT_SCROLL_CAPTURE_HOTKEY,
    DEFAULT_CANCEL_HOTKEY,
    DEFAULT_SAVE_HOTKEY,
)


# ==========================================================
# Capture Settings
# ==========================================================

@dataclass
class CaptureConfig:
    fps: int = DEFAULT_CAPTURE_FPS
    delay: float = DEFAULT_CAPTURE_DELAY

    include_cursor: bool = False

    play_shutter_sound: bool = False

    show_flash_animation: bool = True

    remember_last_region: bool = True


# ==========================================================
# Auto Scroll
# ==========================================================

@dataclass
class AutoScrollConfig:
    enabled: bool = False

    scroll_delay: float = DEFAULT_SCROLL_DELAY

    scroll_step: int = DEFAULT_SCROLL_STEP

    adaptive_speed: bool = True

    detect_page_end: bool = True

    smart_overlap: bool = True


# ==========================================================
# Preview
# ==========================================================

@dataclass
class PreviewConfig:
    zoom: float = 1.0

    smooth_zoom: bool = True

    show_grid: bool = False

    show_guidelines: bool = True


# ==========================================================
# Export
# ==========================================================

@dataclass
class ExportConfig:
    default_format: str = "png"

    jpeg_quality: int = DEFAULT_JPEG_QUALITY

    png_compression: int = DEFAULT_PNG_COMPRESSION

    overwrite_existing: bool = False

    open_after_export: bool = False

    copy_to_clipboard: bool = False


# ==========================================================
# OCR
# ==========================================================

@dataclass
class OCRConfig:
    enabled: bool = False

    language: str = "eng"

    searchable_pdf: bool = True


# ==========================================================
# UI
# ==========================================================

@dataclass
class UIConfig:
    theme: str = DEFAULT_THEME

    remember_window_state: bool = True

    show_tips: bool = True

    animations: bool = True

    language: str = "en"


# ==========================================================
# Hotkeys
# ==========================================================

@dataclass
class HotkeyConfig:
    capture: str = DEFAULT_CAPTURE_HOTKEY

    scrolling_capture: str = DEFAULT_SCROLL_CAPTURE_HOTKEY

    cancel: str = DEFAULT_CANCEL_HOTKEY

    save: str = DEFAULT_SAVE_HOTKEY


# ==========================================================
# History
# ==========================================================

@dataclass
class HistoryConfig:
    max_recent_projects: int = 20

    auto_save_sessions: bool = True

    restore_last_session: bool = True


# ==========================================================
# Root Configuration
# ==========================================================

@dataclass
class AppConfig:
    version: str = VERSION_STRING

    capture: CaptureConfig = field(default_factory=CaptureConfig)

    auto_scroll: AutoScrollConfig = field(default_factory=AutoScrollConfig)

    preview: PreviewConfig = field(default_factory=PreviewConfig)

    export: ExportConfig = field(default_factory=ExportConfig)

    ocr: OCRConfig = field(default_factory=OCRConfig)

    ui: UIConfig = field(default_factory=UIConfig)

    hotkeys: HotkeyConfig = field(default_factory=HotkeyConfig)

    history: HistoryConfig = field(default_factory=HistoryConfig)