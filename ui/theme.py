"""
ScrollSnap
==========

UI Theme

Loads the active color theme from `assets/themes/<name>.json`
(matching `constants.AVAILABLE_THEMES`) and exposes it as module-
level names so existing UI code (`theme.BG`, `theme.ACCENT`, ...)
keeps working unchanged. Call `set_theme(name)` to switch themes
at runtime for windows opened afterwards.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from constants import AVAILABLE_THEMES, DEFAULT_THEME, THEMES_DIR


_FALLBACK_COLORS = {
    "bg": "#0a0a0f",
    "surface": "#12121a",
    "surface2": "#1c1c28",
    "border": "#2a2a3d",
    "accent": "#00e5ff",
    "accent2": "#5bc0be",
    "success": "#00ff88",
    "warning": "#ffb800",
    "danger": "#ff3b30",
    "text": "#e8e8f0",
    "muted": "#6b6b8a",
    "fog_bg": "#111118",
}

_FALLBACK_FONT = {"family": "Segoe UI", "mono": "Courier"}


def _load_theme_file(name: str) -> dict[str, Any] | None:

    path = THEMES_DIR / f"{name}.json"

    if not path.exists():
        return None

    try:

        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    except (json.JSONDecodeError, OSError):
        return None


def _apply(name: str) -> None:
    """
    Populate every module-level color/font/style constant from
    the named theme, falling back to the built-in dark palette
    for anything missing.
    """

    module = sys.modules[__name__]

    data = _load_theme_file(name) or {}

    colors = {**_FALLBACK_COLORS, **data.get("colors", {})}

    font = {**_FALLBACK_FONT, **data.get("font", {})}

    module.CURRENT_THEME = data.get("name", name)

    module.BG = colors["bg"]
    module.SURFACE = colors["surface"]
    module.SURFACE2 = colors["surface2"]
    module.BORDER = colors["border"]
    module.ACCENT = colors["accent"]
    module.ACCENT2 = colors["accent2"]
    module.SUCCESS = colors["success"]
    module.WARNING = colors["warning"]
    module.DANGER = colors["danger"]
    module.TEXT = colors["text"]
    module.MUTED = colors["muted"]
    module.FOG_BG = colors["fog_bg"]

    module.FONT_FAMILY = font["family"]
    module.FONT_MONO = font["mono"]

    module.BUTTON_STYLE = {
        "bg": module.SURFACE2,
        "fg": module.TEXT,
        "activebackground": module.ACCENT,
        "activeforeground": module.BG,
        "relief": "flat",
        "borderwidth": 0,
        "highlightthickness": 0,
        "font": (module.FONT_FAMILY, 10, "bold"),
        "cursor": "hand2",
        "padx": 12,
        "pady": 6,
    }

    module.ACCENT_BUTTON_STYLE = {
        **module.BUTTON_STYLE,
        "bg": module.ACCENT,
        "fg": module.BG,
        "activebackground": module.ACCENT2,
    }

    module.DANGER_BUTTON_STYLE = {
        **module.BUTTON_STYLE,
        "bg": module.DANGER,
        "fg": "#ffffff",
    }


def set_theme(name: str) -> None:
    """
    Switch the active theme. Widgets already built with the old
    style dicts won't restyle themselves automatically (Tkinter
    has no live theming), but any window opened after this call
    will use the new palette.
    """

    if name not in AVAILABLE_THEMES:
        name = DEFAULT_THEME

    _apply(name)


def apply_window_theme(window) -> None:
    """
    Apply the base background color to a Tk/Toplevel window.
    """

    window.configure(bg=BG)


_apply(DEFAULT_THEME)
