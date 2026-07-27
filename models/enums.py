"""
ScrollSnap Enumerations
=======================

Centralized enums shared across the application.

These replace magic strings throughout the codebase.
"""

from __future__ import annotations

from enum import Enum, auto


class CaptureMode(Enum):
    """Available capture modes."""

    REGION = auto()
    WINDOW = auto()
    FULLSCREEN = auto()
    SCROLLING = auto()
    SHAPE = auto()


class ShapeType(Enum):
    """Supported selection shapes."""

    RECTANGLE = auto()
    ROUNDED_RECTANGLE = auto()
    ELLIPSE = auto()
    CIRCLE = auto()
    POLYGON = auto()
    FREEHAND = auto()
    BEZIER = auto()
    STAR = auto()


class ExportFormat(Enum):
    """Supported export formats."""

    PNG = auto()
    JPEG = auto()
    WEBP = auto()
    TIFF = auto()
    PDF = auto()


class CaptureStatus(Enum):
    """Capture session state."""

    IDLE = auto()
    READY = auto()
    CAPTURING = auto()
    STITCHING = auto()
    PREVIEW = auto()
    EXPORTING = auto()
    COMPLETED = auto()
    CANCELLED = auto()
    FAILED = auto()


class Theme(Enum):
    """Available application themes."""

    DARK = auto()
    LIGHT = auto()
    CYBER = auto()


class NotificationLevel(Enum):
    """Notification severity."""

    INFO = auto()
    SUCCESS = auto()
    WARNING = auto()
    ERROR = auto()