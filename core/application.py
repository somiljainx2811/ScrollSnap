"""
ScrollSnap Application Kernel
=============================

The central application object.

Responsibilities
----------------
- Owns application-wide state
- Provides dependency resolution
- Coordinates lifecycle
- Exposes event bus
- Stores configuration

This is the root object for the entire application.
"""

from __future__ import annotations

from config import AppConfig
from core.dependency_container import DependencyContainer
from core.event_bus import EventBus
from core.lifecycle import LifecycleManager


class Application:
    """
    Root application object.

    Every subsystem is accessed through this class.
    """

    def __init__(self) -> None:

        self._container = DependencyContainer()

        self._event_bus = EventBus()

        self._lifecycle = LifecycleManager()

        self._config = AppConfig()

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def container(self) -> DependencyContainer:
        return self._container

    @property
    def events(self) -> EventBus:
        return self._event_bus

    @property
    def lifecycle(self) -> LifecycleManager:
        return self._lifecycle

    @property
    def config(self) -> AppConfig:
        return self._config

    # --------------------------------------------------
    # Startup / Shutdown
    # --------------------------------------------------

    def startup(self) -> None:
        """
        Start the application.
        """

        self.lifecycle.startup()

    def shutdown(self) -> None:
        """
        Shutdown the application.
        """

        self.lifecycle.shutdown()


# ----------------------------------------------------------
# Global Application Instance
# ----------------------------------------------------------

app = Application()