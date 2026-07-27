"""
ScrollSnap
==========

Plugin API

The contract every ScrollSnap plugin implements, plus the
`PluginContext` handed to each one on activation.

Plugins hook into the application purely through the existing
`core.event_bus` - the same bus every controller already
publishes to (`capture.started`, `capture.frame_captured`,
`stitch.completed`, `export.completed`, `ocr.extracted`, ...).
This keeps plugins decoupled from internals: a plugin never
imports a controller directly, it only reacts to events and
uses the small set of capabilities exposed on `PluginContext`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from config import AppConfig
from core.event_bus import EventBus


@dataclass(slots=True)
class PluginContext:
    """
    Capabilities made available to every plugin. Kept small and
    stable on purpose - plugins should not need application
    internals beyond this.
    """

    event_bus: EventBus

    config: AppConfig

    notify: Callable[[str, str], None]
    """notify(title, message) - shows a non-blocking notification."""

    copy_text_to_clipboard: Callable[[str], None]


class Plugin(ABC):
    """
    Base class for every ScrollSnap plugin.
    """

    name: str = "Unnamed Plugin"

    version: str = "0.1.0"

    description: str = ""

    def __init__(self) -> None:
        self._subscriptions: list[tuple[str, Callable]] = []

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    @abstractmethod
    def activate(self, context: PluginContext) -> None:
        """
        Called once when the plugin is loaded. Subclasses should
        call `self._subscribe(context, event, handler)` here for
        every event they care about, so `deactivate()` can clean
        up automatically.
        """

        raise NotImplementedError

    def deactivate(self) -> None:
        """
        Called on shutdown (or if the plugin is disabled).
        Unsubscribes from every event registered via
        `_subscribe()`. Override to add custom teardown, calling
        `super().deactivate()` too.
        """

        for event_name, handler in self._subscriptions:
            self._context.event_bus.unsubscribe(event_name, handler)

        self._subscriptions.clear()

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def _subscribe(
        self,
        context: PluginContext,
        event_name: str,
        handler: Callable,
    ) -> None:

        self._context = context

        context.event_bus.subscribe(event_name, handler)

        self._subscriptions.append((event_name, handler))

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r})"
