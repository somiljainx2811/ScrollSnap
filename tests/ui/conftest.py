"""
Shared fixtures for UI tests (all require a real or virtual
display - see `tests.conftest.requires_display`).
"""

from __future__ import annotations

import pytest


@pytest.fixture
def tk_root():

    import tkinter as tk

    root = tk.Tk()

    root.withdraw()

    yield root

    root.destroy()


class FakeEvent:
    """Minimal stand-in for a tkinter mouse event."""

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
