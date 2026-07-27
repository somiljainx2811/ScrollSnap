"""
ScrollSnap Version Information
==============================

Contains application version metadata.

This file should remain dependency-free so it can be imported anywhere,
including setup scripts and packaging tools.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Version:
    """
    Represents a semantic version.

    Format:
        MAJOR.MINOR.PATCH
    """

    major: int
    minor: int
    patch: int

    @property
    def string(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @property
    def tuple(self) -> tuple[int, int, int]:
        return self.major, self.minor, self.patch

    def __str__(self) -> str:
        return self.string


# ---------------------------------------------------------------------
# Current Version
# ---------------------------------------------------------------------

APP_VERSION = Version(
    major=0,
    minor=1,
    patch=0,
)

# ---------------------------------------------------------------------
# Application Metadata
# ---------------------------------------------------------------------

APP_NAME = "ScrollSnap"

APP_DESCRIPTION = (
    "Advanced scrolling screenshot and smart image stitching application."
)

APP_AUTHOR = "Mark"

APP_LICENSE = "MIT"

APP_COPYRIGHT = "© 2026 ScrollSnap Project"

APP_WEBSITE = "https://github.com/<your-username>/ScrollSnap"

APP_REPOSITORY = APP_WEBSITE

APP_USER_AGENT = f"{APP_NAME}/{APP_VERSION.string}"

VERSION_STRING = APP_VERSION.string