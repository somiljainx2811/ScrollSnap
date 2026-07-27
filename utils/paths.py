"""
ScrollSnap Path Utilities
=========================

Centralized filesystem path management.

Responsibilities
----------------
- Application directories
- User data directories
- Cache locations
- Log locations
- Export locations
- Project locations

No directory is created automatically except through ensure_* functions.
"""

from __future__ import annotations

from pathlib import Path
import platform

from constants import (
    APP_NAME,
    CACHE_DIR_NAME,
    SESSION_DIR_NAME,
    EXPORT_DIR_NAME,
    PROJECT_DIR_NAME,
    THUMBNAIL_DIR_NAME,
    LOG_DIR_NAME,
)


# ==========================================================
# Operating System
# ==========================================================

SYSTEM = platform.system()


# ==========================================================
# User Directories
# ==========================================================

HOME = Path.home()

if SYSTEM == "Windows":
    BASE_DATA = HOME / "AppData" / "Local" / APP_NAME

elif SYSTEM == "Darwin":
    BASE_DATA = (
        HOME
        / "Library"
        / "Application Support"
        / APP_NAME
    )

else:
    BASE_DATA = HOME / ".local" / "share" / APP_NAME


# ==========================================================
# Application Directories
# ==========================================================

CACHE_DIR = BASE_DATA / CACHE_DIR_NAME

LOG_DIR = BASE_DATA / LOG_DIR_NAME

SESSION_DIR = BASE_DATA / SESSION_DIR_NAME

PROJECT_DIR = BASE_DATA / PROJECT_DIR_NAME

EXPORT_DIR = BASE_DATA / EXPORT_DIR_NAME

THUMBNAIL_DIR = CACHE_DIR / THUMBNAIL_DIR_NAME

TEMP_DIR = CACHE_DIR / "temp"

CONFIG_FILE = BASE_DATA / "config.json"

DATABASE_FILE = BASE_DATA / "scrollsnap.db"


# ==========================================================
# Directory Helpers
# ==========================================================

ALL_DIRECTORIES = (
    BASE_DATA,
    CACHE_DIR,
    LOG_DIR,
    SESSION_DIR,
    PROJECT_DIR,
    EXPORT_DIR,
    THUMBNAIL_DIR,
    TEMP_DIR,
)


def ensure_directory(path: Path) -> Path:
    """
    Create a directory if it doesn't already exist.

    Returns the same Path object for convenience.
    """

    path.mkdir(parents=True, exist_ok=True)

    return path


def ensure_all_directories() -> None:
    """
    Create every application directory.
    """

    for directory in ALL_DIRECTORIES:
        ensure_directory(directory)


# ==========================================================
# Runtime Helpers
# ==========================================================

def project_file(name: str) -> Path:
    """
    Returns a project file path.

    Example:
        project_file("comic.ssproj")
    """

    return PROJECT_DIR / name


def session_file(name: str) -> Path:
    return SESSION_DIR / name


def export_file(name: str) -> Path:
    return EXPORT_DIR / name


def cache_file(name: str) -> Path:
    return CACHE_DIR / name


def thumbnail_file(name: str) -> Path:
    return THUMBNAIL_DIR / name


def temporary_file(name: str) -> Path:
    return TEMP_DIR / name