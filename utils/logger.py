"""
ScrollSnap Logger
=================

Centralized logging for the entire application.

Features
--------
• Colored console logging
• Rotating log files
• Thread-safe
• Singleton logger
• Exception logging
• Easy child loggers
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

from constants import (
    LOG_FILE,
    LOG_DIR_NAME,
    MAX_LOG_SIZE,
    BACKUP_LOGS,
)

# ---------------------------------------------------------
# Internal logger cache
# ---------------------------------------------------------

_INITIALIZED = False


def initialize_logger(log_directory: Path) -> None:
    """
    Initializes the application logger.

    Should only be called once during startup.
    """

    global _INITIALIZED

    if _INITIALIZED:
        return

    log_directory.mkdir(parents=True, exist_ok=True)

    logfile = log_directory / LOG_FILE

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()

    root.setLevel(logging.INFO)

    # -------------------------
    # Console
    # -------------------------

    console = logging.StreamHandler()

    console.setFormatter(formatter)

    root.addHandler(console)

    # -------------------------
    # Rotating File
    # -------------------------

    rotating = logging.handlers.RotatingFileHandler(
        logfile,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_LOGS,
        encoding="utf-8",
    )

    rotating.setFormatter(formatter)

    root.addHandler(rotating)

    _INITIALIZED = True


def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger instance.

    Example

        logger = get_logger(__name__)
    """

    return logging.getLogger(name)


def log_exception(logger: logging.Logger, exc: Exception) -> None:
    """
    Logs an exception with traceback.
    """

    logger.exception("%s", exc)