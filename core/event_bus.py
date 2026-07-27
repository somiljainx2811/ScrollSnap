"""
ScrollSnap Event Bus
====================

A lightweight, thread-safe publish/subscribe event system.

Goals
-----
- Loose coupling between modules
- No circular imports
- Type-safe events
- Thread-safe subscriptions
- Simple API

Example
-------
event_bus.subscribe("capture.started", on_capture_started)

event_bus.publish("capture.started", session)
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from threading import RLock
from typing import Any, Callable


# ---------------------------------------------------------
# Event Object
# ---------------------------------------------------------

@dataclass(frozen=True)
class Event:
    """
    Represents an application event.
    """

    name: str

    data: Any = None


# ---------------------------------------------------------
# Event Bus
# ---------------------------------------------------------

class EventBus:

    def __init__(self) -> None:

        self._listeners = defaultdict(list)

        self._lock = RLock()

    # -----------------------------------------------------

    def subscribe(
        self,
        event_name: str,
        callback: Callable[[Event], None],
    ) -> None:
        """
        Subscribe to an event.
        """

        with self._lock:

            if callback not in self._listeners[event_name]:

                self._listeners[event_name].append(callback)

    # -----------------------------------------------------

    def unsubscribe(
        self,
        event_name: str,
        callback: Callable[[Event], None],
    ) -> None:
        """
        Remove a listener.
        """

        with self._lock:

            if callback in self._listeners[event_name]:

                self._listeners[event_name].remove(callback)

    # -----------------------------------------------------

    def publish(
        self,
        event_name: str,
        data: Any = None,
    ) -> None:
        """
        Publish an event.
        """

        event = Event(event_name, data)

        with self._lock:

            listeners = list(self._listeners[event_name])

        for listener in listeners:

            listener(event)

    # -----------------------------------------------------

    def clear(self) -> None:
        """
        Remove all listeners.
        """

        with self._lock:

            self._listeners.clear()

    # -----------------------------------------------------

    def listener_count(
        self,
        event_name: str,
    ) -> int:

        with self._lock:

            return len(self._listeners[event_name])


# ---------------------------------------------------------
# Global Event Bus
# ---------------------------------------------------------

event_bus = EventBus()