"""
ScrollSnap
==========

Global Hotkey Manager

Provides a platform-independent hotkey abstraction.

Platform implementations:

    platform/windows/hotkeys.py
    platform/linux/hotkeys.py
    platform/macos/hotkeys.py

Responsibilities:
- Register shortcuts
- Remove shortcuts
- Dispatch callbacks
- Manage application commands

This module does not handle OS keyboard hooks directly.
"""


from __future__ import annotations

from abc import ABC, abstractmethod

from dataclasses import dataclass

from threading import RLock

from typing import Callable


HotkeyCallback = Callable[[], None]


@dataclass(slots=True, frozen=True)
class Hotkey:
    """
    Represents a keyboard shortcut.
    """

    key: str

    modifiers: tuple[str, ...] = ()


class HotkeyManager(ABC):
    """
    Abstract global hotkey manager.
    """

    # ---------------------------------------------------------
    # Registration
    # ---------------------------------------------------------

    @abstractmethod
    def register(
        self,
        hotkey: Hotkey,
        callback: HotkeyCallback,
    ) -> None:
        """
        Register a global shortcut.
        """
        raise NotImplementedError


    @abstractmethod
    def unregister(
        self,
        hotkey: Hotkey,
    ) -> None:
        """
        Remove a shortcut.
        """
        raise NotImplementedError


    @abstractmethod
    def start(
        self,
    ) -> None:
        """
        Start listening.
        """
        raise NotImplementedError


    @abstractmethod
    def stop(
        self,
    ) -> None:
        """
        Stop listening.
        """
        raise NotImplementedError


class DefaultHotkeys:
    """
    Standard ScrollSnap shortcuts.

    UI layer can override these.
    """

    START_CAPTURE = Hotkey(
        key="s",
        modifiers=("ctrl", "shift"),
    )

    STOP_CAPTURE = Hotkey(
        key="escape",
    )

    PAUSE_CAPTURE = Hotkey(
        key="space",
    )

    CANCEL_CAPTURE = Hotkey(
        key="c",
        modifiers=("ctrl", "shift"),
    )


class HotkeyRegistry:
    """
    Thread-safe hotkey callback registry.

    Used internally by platform implementations.
    """

    def __init__(self) -> None:

        self._callbacks: dict[
            Hotkey,
            HotkeyCallback,
        ] = {}

        self._lock = RLock()


    def add(
        self,
        hotkey: Hotkey,
        callback: HotkeyCallback,
    ) -> None:

        with self._lock:

            self._callbacks[hotkey] = callback


    def remove(
        self,
        hotkey: Hotkey,
    ) -> None:

        with self._lock:

            self._callbacks.pop(
                hotkey,
                None,
            )


    def trigger(
        self,
        hotkey: Hotkey,
    ) -> None:

        with self._lock:

            callback = self._callbacks.get(
                hotkey
            )

        if callback:
            callback()


    def clear(
        self,
    ) -> None:

        with self._lock:
            self._callbacks.clear()