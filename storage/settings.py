"""
ScrollSnap
==========

Settings Storage

Provides persistent storage for application preferences.

This module is intentionally independent from the UI. It simply loads
and saves the Preferences model as JSON.

Future versions can transparently migrate old configuration files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models.preferences import Preferences


DEFAULT_SETTINGS_FILENAME = "settings.json"


class SettingsStorage:
    """
    Persistent storage for application settings.
    """

    def __init__(
        self,
        directory: Path,
        filename: str = DEFAULT_SETTINGS_FILENAME,
    ) -> None:

        self._directory = Path(directory)
        self._path = self._directory / filename

    @property
    def path(self) -> Path:
        """
        Full path to the settings file.
        """
        return self._path

    @property
    def exists(self) -> bool:
        """
        True if the settings file exists.
        """
        return self._path.exists()

    def load(self) -> Preferences:
        """
        Load preferences from disk.

        Returns
        -------
        Preferences
            Loaded preferences, or default preferences if the file
            does not exist.
        """
        if not self.exists:
            return Preferences()

        with self._path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data: dict[str, Any] = json.load(file)

        return Preferences.from_dict(data)

    def save(
        self,
        preferences: Preferences,
    ) -> None:
        """
        Save preferences to disk.
        """
        self._directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self._path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                preferences.to_dict(),
                file,
                indent=4,
                ensure_ascii=False,
            )

    def reset(self) -> Preferences:
        """
        Reset settings to defaults and save them.

        Returns
        -------
        Preferences
            Newly created default preferences.
        """
        preferences = Preferences()
        self.save(preferences)
        return preferences

    def delete(self) -> None:
        """
        Delete the settings file if it exists.
        """
        if self.exists:
            self._path.unlink()