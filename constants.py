"""
ScrollSnap Constants
====================

Global immutable constants used throughout the application.

Rules:
- Do NOT store user settings here.
- Do NOT store runtime state.
- Do NOT import project modules.
- Keep this file dependency-free.
"""

from pathlib import Path

# ==========================================================
# Application
# ==========================================================

APP_NAME = "ScrollSnap"

ORGANIZATION = "ScrollSnap"

CONFIG_VERSION = 1

# ==========================================================
# Directories
# ==========================================================

ROOT_DIR = Path(__file__).resolve().parent

ASSETS_DIR = ROOT_DIR / "assets"

ICONS_DIR = ASSETS_DIR / "icons"

FONTS_DIR = ASSETS_DIR / "fonts"

CURSORS_DIR = ASSETS_DIR / "cursors"

THEMES_DIR = ASSETS_DIR / "themes"

TEMPLATES_DIR = ASSETS_DIR / "templates"

ANIMATIONS_DIR = ASSETS_DIR / "animations"

CACHE_DIR_NAME = "cache"

SESSION_DIR_NAME = "sessions"

THUMBNAIL_DIR_NAME = "thumbnails"

LOG_DIR_NAME = "logs"

EXPORT_DIR_NAME = "exports"

PROJECT_DIR_NAME = "projects"

# ==========================================================
# Themes
# ==========================================================

DEFAULT_THEME = "dark"

AVAILABLE_THEMES = (
    "dark",
    "light",
    "cyber",
)

# ==========================================================
# Capture
# ==========================================================

DEFAULT_CAPTURE_FPS = 30

MIN_CAPTURE_FPS = 5

MAX_CAPTURE_FPS = 240

DEFAULT_CAPTURE_DELAY = 0

DEFAULT_SCROLL_DELAY = 0.30

DEFAULT_SCROLL_STEP = 3

MAX_CAPTURE_HISTORY = 100

# ==========================================================
# Image
# ==========================================================

DEFAULT_JPEG_QUALITY = 95

DEFAULT_PNG_COMPRESSION = 6

MAX_ZOOM = 32.0

MIN_ZOOM = 0.05

DEFAULT_ZOOM = 1.0

THUMBNAIL_SIZE = (256, 256)

# ==========================================================
# Export Formats
# ==========================================================

EXPORT_PNG = "png"

EXPORT_JPEG = "jpeg"

EXPORT_WEBP = "webp"

EXPORT_TIFF = "tiff"

EXPORT_PDF = "pdf"

SUPPORTED_EXPORTS = (
    EXPORT_PNG,
    EXPORT_JPEG,
    EXPORT_WEBP,
    EXPORT_TIFF,
    EXPORT_PDF,
)

# ==========================================================
# Image Extensions
# ==========================================================

SUPPORTED_IMAGE_EXTENSIONS = (
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp",
)

# ==========================================================
# Project
# ==========================================================

PROJECT_EXTENSION = ".ssproj"

SESSION_EXTENSION = ".sssession"

# ==========================================================
# Capture Modes
# ==========================================================

CAPTURE_REGION = "region"

CAPTURE_WINDOW = "window"

CAPTURE_FULLSCREEN = "fullscreen"

CAPTURE_SHAPE = "shape"

CAPTURE_SCROLLING = "scrolling"

# ==========================================================
# Shapes
# ==========================================================

SHAPE_RECTANGLE = "rectangle"

SHAPE_ROUNDED_RECTANGLE = "rounded_rectangle"

SHAPE_ELLIPSE = "ellipse"

SHAPE_CIRCLE = "circle"

SHAPE_POLYGON = "polygon"

SHAPE_FREEHAND = "freehand"

SHAPE_BEZIER = "bezier"

SHAPE_STAR = "star"

SUPPORTED_SHAPES = (
    SHAPE_RECTANGLE,
    SHAPE_ROUNDED_RECTANGLE,
    SHAPE_ELLIPSE,
    SHAPE_CIRCLE,
    SHAPE_POLYGON,
    SHAPE_FREEHAND,
    SHAPE_BEZIER,
    SHAPE_STAR,
)

# ==========================================================
# OCR
# ==========================================================

OCR_LANGUAGE_DEFAULT = "eng"

# ==========================================================
# Logging
# ==========================================================

LOG_FILE = "scrollsnap.log"

MAX_LOG_SIZE = 10 * 1024 * 1024

BACKUP_LOGS = 5

# ==========================================================
# Autosave
# ==========================================================

AUTOSAVE_INTERVAL_SECONDS = 60

# ==========================================================
# UI
# ==========================================================

STATUSBAR_TIMEOUT = 3000

DEFAULT_BORDER_THICKNESS = 2

DEFAULT_HANDLE_SIZE = 8

DEFAULT_GRID_SIZE = 10

# ==========================================================
# Notifications
# ==========================================================

NOTIFICATION_SHORT = 2000

NOTIFICATION_LONG = 5000

# ==========================================================
# Clipboard
# ==========================================================

CLIPBOARD_IMAGE = "image"

CLIPBOARD_TEXT = "text"

# ==========================================================
# Hotkeys
# ==========================================================

DEFAULT_CAPTURE_HOTKEY = "Ctrl+Shift+A"

DEFAULT_SCROLL_CAPTURE_HOTKEY = "Ctrl+Shift+S"

DEFAULT_CANCEL_HOTKEY = "Esc"

DEFAULT_SAVE_HOTKEY = "Ctrl+S"

# ==========================================================
# Exit Codes
# ==========================================================

EXIT_SUCCESS = 0

EXIT_FAILURE = 1

EXIT_RESTART = 100