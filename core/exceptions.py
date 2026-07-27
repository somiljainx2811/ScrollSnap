"""
ScrollSnap Exception Hierarchy
==============================

Centralized exception classes used throughout the application.

All project-specific exceptions should inherit from ScrollSnapError.
"""

from __future__ import annotations


class ScrollSnapError(Exception):
    """
    Base class for all ScrollSnap exceptions.
    """


# ==========================================================
# Configuration
# ==========================================================

class ConfigurationError(ScrollSnapError):
    """Invalid or corrupted configuration."""


class ConfigurationMigrationError(ConfigurationError):
    """Configuration migration failed."""


# ==========================================================
# Capture
# ==========================================================

class CaptureError(ScrollSnapError):
    """Base capture exception."""


class CaptureInitializationError(CaptureError):
    """Capture engine failed to initialize."""


class ScreenCaptureError(CaptureError):
    """Unable to capture the screen."""


class RegionError(CaptureError):
    """Invalid capture region."""


class AutoScrollError(CaptureError):
    """Auto-scroll operation failed."""


class EndOfPageDetected(AutoScrollError):
    """
    Internal signal indicating that the end of a scrolling page
    has been reached.
    """


# ==========================================================
# Stitching
# ==========================================================

class StitchingError(ScrollSnapError):
    """Image stitching failed."""


class OverlapNotFoundError(StitchingError):
    """No overlap could be detected between frames."""


class AlignmentError(StitchingError):
    """Image alignment failed."""


# ==========================================================
# Export
# ==========================================================

class ExportError(ScrollSnapError):
    """Image export failed."""


class UnsupportedFormatError(ExportError):
    """Requested export format is not supported."""


# ==========================================================
# OCR
# ==========================================================

class OCRError(ScrollSnapError):
    """OCR operation failed."""


# ==========================================================
# Plugins
# ==========================================================

class PluginError(ScrollSnapError):
    """Plugin system error."""


class PluginLoadError(PluginError):
    """Unable to load plugin."""


# ==========================================================
# Storage
# ==========================================================

class StorageError(ScrollSnapError):
    """Persistent storage operation failed."""


class ProjectLoadError(StorageError):
    """Project could not be loaded."""


class ProjectSaveError(StorageError):
    """Project could not be saved."""


# ==========================================================
# Preview
# ==========================================================

class PreviewError(ScrollSnapError):
    """Preview subsystem error."""


# ==========================================================
# Validation
# ==========================================================

class ValidationError(ScrollSnapError):
    """Invalid user or application data."""