"""
ScrollSnap
==========

Pynput Hotkey Backend

Concrete, cross-platform implementation of
`capture.input.hotkeys.HotkeyManager` using
`pynput.keyboard.GlobalHotKeys`.
"""

from __future__ import annotations

from pynput import keyboard

from capture.input.hotkeys import Hotkey, HotkeyManager


_MODIFIER_TOKENS = {
    "ctrl": "<ctrl>",
    "control": "<ctrl>",
    "shift": "<shift>",
    "alt": "<alt>",
    "cmd": "<cmd>",
    "super": "<cmd>",
}


def _to_pynput_string(hotkey: Hotkey) -> str:
    """
    Convert a `Hotkey(key="s", modifiers=("ctrl", "shift"))`
    into pynput's `GlobalHotKeys` string format, e.g.
    `"<ctrl>+<shift>+s"`.
    """

    tokens = [
        _MODIFIER_TOKENS.get(mod.lower(), f"<{mod.lower()}>")
        for mod in hotkey.modifiers
    ]

    key = hotkey.key.lower()

    special = {
        "escape": "<esc>",
        "esc": "<esc>",
        "space": "<space>",
        "enter": "<enter>",
        "tab": "<tab>",
    }.get(key, key)

    tokens.append(special)

    return "+".join(tokens)


class PynputHotkeyManager(HotkeyManager):
    """
    Concrete global hotkey manager.
    """

    def __init__(self) -> None:

        self._bindings: dict[Hotkey, str] = {}

        self._callbacks: dict[str, callable] = {}

        self._listener: keyboard.GlobalHotKeys | None = None

    # ---------------------------------------------------------
    # Registration
    # ---------------------------------------------------------

    def register(self, hotkey: Hotkey, callback) -> None:

        combo = _to_pynput_string(hotkey)

        self._bindings[hotkey] = combo

        self._callbacks[combo] = callback

        if self._listener is not None:
            self._restart()

    def unregister(self, hotkey: Hotkey) -> None:

        combo = self._bindings.pop(hotkey, None)

        if combo is not None:
            self._callbacks.pop(combo, None)

        if self._listener is not None:
            self._restart()

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def start(self) -> None:

        if self._listener is not None:
            return

        if not self._callbacks:
            return

        self._listener = keyboard.GlobalHotKeys(
            dict(self._callbacks)
        )

        self._listener.start()

    def stop(self) -> None:

        if self._listener is None:
            return

        self._listener.stop()

        self._listener = None

    def _restart(self) -> None:

        self.stop()

        self.start()

    def __repr__(self) -> str:

        return (
            f"PynputHotkeyManager(bindings={len(self._bindings)})"
        )
