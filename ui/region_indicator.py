"""
ScrollSnap
==========

Region Indicator

A persistent on-screen border marking the currently selected
capture region.

Unlike `SelectionOverlay` (which only exists while the user is
dragging out a region and is destroyed the moment they confirm
it), `RegionIndicator` is meant to stay visible continuously from
the moment a region is selected through an entire capture
session, so the user always has a clear answer to "what exactly
is ScrollSnap capturing right now?".

Implementation notes
---------------------
The border is drawn as four thin, borderless, always-on-top
`Toplevel` strips (top/bottom/left/right) placed just outside the
selected rectangle, rather than a single window with a
transparent center. This keeps it simple and portable across
Windows/Linux (a true transparent-center window needs
per-platform tricks - e.g. `-transparentcolor` on Windows only -
whereas four solid strips render identically everywhere Tkinter
does). Each strip is only a few pixels thick, so it does not
meaningfully block clicks on the content underneath.
"""

from __future__ import annotations

import tkinter as tk

from models.rectangle import Rectangle
from ui import theme


THICKNESS = 3


class RegionIndicator:
    """
    Persistent, click-through-ish border around a capture region.
    """

    def __init__(self, master: tk.Misc) -> None:

        self._master = master

        self._strips: dict[str, tk.Toplevel] = {}

        self._rectangle: Rectangle | None = None

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    @property
    def visible(self) -> bool:
        return bool(self._strips)

    def show(
        self,
        rectangle: Rectangle,
        color: str | None = None,
    ) -> None:
        """
        Show (or move, if already showing) the border around
        `rectangle`.
        """

        self._rectangle = rectangle

        if not self._strips:
            self._create_strips()

        self._position_strips()

        self.set_color(color or theme.ACCENT)

    def set_color(self, color: str) -> None:
        """
        Recolor the border in place (e.g. switch to a "recording"
        color while a scrolling capture is running).
        """

        for strip in self._strips.values():
            strip.configure(bg=color)

    def hide(self) -> None:
        """
        Remove the border entirely.
        """

        for strip in self._strips.values():
            strip.destroy()

        self._strips.clear()

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _create_strips(self) -> None:

        for name in ("top", "bottom", "left", "right"):

            strip = tk.Toplevel(self._master)

            strip.overrideredirect(True)

            strip.attributes("-topmost", True)

            try:
                # Best-effort: keeps the strip from ever taking
                # keyboard/mouse focus on platforms that support
                # it. Not fatal if unavailable.
                strip.attributes("-disabled", True)
            except tk.TclError:
                pass

            strip.configure(bg=theme.ACCENT)

            self._strips[name] = strip

    def _position_strips(self) -> None:

        if self._rectangle is None or not self._strips:
            return

        x1 = int(self._rectangle.left)
        y1 = int(self._rectangle.top)
        x2 = int(self._rectangle.right)
        y2 = int(self._rectangle.bottom)

        width = x2 - x1
        height = y2 - y1

        t = THICKNESS

        geometries = {
            "top": (x1 - t, y1 - t, width + 2 * t, t),
            "bottom": (x1 - t, y2, width + 2 * t, t),
            "left": (x1 - t, y1 - t, t, height + 2 * t),
            "right": (x2, y1 - t, t, height + 2 * t),
        }

        for name, (gx, gy, gw, gh) in geometries.items():

            gw = max(1, gw)
            gh = max(1, gh)

            self._strips[name].geometry(f"{gw}x{gh}+{gx}+{gy}")
