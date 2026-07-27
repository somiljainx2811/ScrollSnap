"""
ScrollSnap
==========

Event System

A lightweight publish/subscribe event dispatcher used throughout
the application to decouple components.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from threading import RLock
from typing import Any


EventHandler = Callable[..., None]


class EventBus:
    """
    Thread-safe event bus.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._lock = RLock()

    def subscribe(
        self,
        event: str,
        handler: EventHandler,
    ) -> None:
        """
        Register a handler for an event.
        """
        with self._lock:
            if handler not in self._handlers[event]:
                self._handlers[event].append(handler)

    def unsubscribe(
        self,
        event: str,
        handler: EventHandler,
    ) -> None:
        """
        Remove a handler.
        """
        with self._lock:
            if handler in self._handlers[event]:
                self._handlers[event].remove(handler)

    def publish(
        self,
        event: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Notify all subscribers.
        """
        with self._lock:
            handlers = list(self._handlers.get(event, []))

        for handler in handlers:
            handler(*args, **kwargs)

    def clear(self) -> None:
        """
        Remove all subscriptions.
        """
        with self._lock:
            self._handlers.clear()

    def has_subscribers(self, event: str) -> bool:
        """
        Check if an event has subscribers.
        """
        with self._lock:
            return bool(self._handlers.get(event))


# Global application event bus
event_bus = EventBus()