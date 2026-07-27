"""
ScrollSnap
==========

Config

Thin re-export module.

`settings.py` defines the actual configuration schema
(`AppConfig` and its nested sections). This module exists only
because `core/application.py` (and anything else wiring up the
application root) imports from `config`, matching the
`config.py` module named in the architecture document.

Keeping the schema itself in `settings.py` (no filesystem/UI
imports) and re-exporting it here avoids a circular import
between `core/application.py` and a `config.py` that would
otherwise need to import UI/storage concerns.
"""

from __future__ import annotations

from settings import (
    AppConfig,
    AutoScrollConfig,
    CaptureConfig,
    ExportConfig,
    HistoryConfig,
    HotkeyConfig,
    OCRConfig,
    PreviewConfig,
    UIConfig,
)

__all__ = [
    "AppConfig",
    "AutoScrollConfig",
    "CaptureConfig",
    "ExportConfig",
    "HistoryConfig",
    "HotkeyConfig",
    "OCRConfig",
    "PreviewConfig",
    "UIConfig",
]
