"""
ScrollSnap
==========

Entry Point

Launches the ScrollSnap desktop application.
"""

from __future__ import annotations

import sys

from constants import LOG_DIR_NAME, ROOT_DIR
from core.application import app
from platforms.dpi import enable_dpi_awareness
from ui.main_window import MainWindow
from utils.logger import get_logger, initialize_logger


initialize_logger(ROOT_DIR / LOG_DIR_NAME)

logger = get_logger(__name__)


def main() -> int:

    if not enable_dpi_awareness():
        logger.warning(
            "Could not enable per-monitor DPI awareness; capture "
            "regions on scaled displays may be misaligned."
        )

    logger.info("Starting ScrollSnap %s", app.config.version)

    app.startup()

    window = MainWindow()

    try:
        window.mainloop()

    finally:
        app.shutdown()

    return 0


if __name__ == "__main__":
    sys.exit(main())
