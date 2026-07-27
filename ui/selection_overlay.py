"""
ScrollSnap
==========

Selection Overlay

Full-screen region selection window with:

- A live magnifier loupe that tracks the cursor while dragging,
  showing a zoomed-in crop of the real screen content plus the
  center pixel's RGB value (precision framing, without needing
  to guess pixel boundaries).
- After the initial drag, eight draggable border handles so the
  region can be fine-tuned (resize from any edge/corner, or drag
  from the middle to reposition) before confirming.
- Correct geometry across multi-monitor virtual desktops: the
  overlay spans the full combined desktop (via `mss`'s monitor-0
  bounding box) rather than assuming a single primary display,
  so selection coordinates always line up with what
  `MssScreenCapture` will actually capture.
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from PIL import Image, ImageTk

from platforms.mss_compat import create_mss
from ui import theme


HANDLE_SIZE = 9
HANDLE_HIT_RADIUS = 10
MAGNIFIER_SIZE = 140
MAGNIFIER_SOURCE = 18
MAGNIFIER_OFFSET = 24
MIN_SELECTION = 12


class SelectionOverlay(tk.Toplevel):
    """
    Full-screen overlay for dragging out (and then fine-tuning) a
    capture region.

    `on_selected` is called with `(x1, y1, x2, y2)` in absolute
    desktop coordinates, or `(None, None, None, None)` if the
    user cancels with Escape.
    """

    def __init__(
        self,
        master: tk.Misc,
        on_selected: Callable[
            [int | None, int | None, int | None, int | None], None
        ],
    ) -> None:

        super().__init__(master)

        self.on_selected = on_selected

        self._mode = "idle"  # idle -> dragging -> adjusting

        self._rect = [0, 0, 0, 0]  # x1, y1, x2, y2 (desktop coords)

        self._active_handle: str | None = None

        self._move_anchor: tuple[int, int] | None = None

        self._magnifier_photo: ImageTk.PhotoImage | None = None

        desktop_left, desktop_top, desktop_width, desktop_height = (
            self._virtual_desktop_bounds()
        )

        self._origin = (desktop_left, desktop_top)

        self._background = self._capture_background()

        self.overrideredirect(True)

        self.geometry(
            f"{desktop_width}x{desktop_height}"
            f"+{desktop_left}+{desktop_top}"
        )

        self.attributes("-topmost", True)

        self.configure(bg=theme.FOG_BG)

        self.lift()

        self.canvas = tk.Canvas(
            self,
            cursor="crosshair",
            bg=theme.FOG_BG,
            highlightthickness=0,
        )

        self.canvas.pack(fill=tk.BOTH, expand=True)

        self._dim_photo = self._make_dim_background(
            desktop_width, desktop_height
        )

        self.canvas.create_image(
            0, 0, anchor="nw", image=self._dim_photo, tags="backdrop"
        )

        self.canvas.create_text(
            desktop_width // 2,
            desktop_height // 2,
            text="Drag to select capture region\nEsc to cancel",
            fill=theme.ACCENT,
            font=(theme.FONT_MONO, 18, "bold"),
            justify=tk.CENTER,
            tags="hint",
        )

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_hover)

        self.bind("<Escape>", lambda _e: self._cancel())
        self.bind("<Return>", lambda _e: self._confirm())

        self.focus_force()

    # ---------------------------------------------------------
    # Desktop / Background Capture
    # ---------------------------------------------------------

    def _virtual_desktop_bounds(self) -> tuple[int, int, int, int]:
        """
        The bounding box of *every* monitor combined, in absolute
        desktop coordinates - this is what `mss` uses internally,
        so using the same source here keeps the overlay and the
        real capture perfectly aligned on multi-monitor setups
        (including monitors positioned left of / above the
        primary, which have negative coordinates).
        """

        with create_mss() as sct:

            combined = sct.monitors[0]

            return (
                combined["left"],
                combined["top"],
                combined["width"],
                combined["height"],
            )

    def _capture_background(self) -> Image.Image:
        """
        Snapshot the real screen content once, before the overlay
        itself is shown, so the magnifier can display genuine
        pixels underneath the cursor rather than the overlay's
        own semi-transparent fog.
        """

        with create_mss() as sct:

            shot = sct.grab(sct.monitors[0])

            return Image.frombytes("RGB", shot.size, shot.rgb)

    def _make_dim_background(
        self, width: int, height: int
    ) -> ImageTk.PhotoImage:

        dimmed = Image.blend(
            self._background,
            Image.new("RGB", self._background.size, (0, 0, 0)),
            alpha=0.55,
        )

        if dimmed.size != (width, height):
            dimmed = dimmed.resize((width, height))

        self._dim_image = dimmed  # keep a ref alongside the PhotoImage

        return ImageTk.PhotoImage(dimmed)

    def _to_local(self, x: int, y: int) -> tuple[int, int]:
        """Desktop coordinates -> overlay-canvas-local coordinates."""

        return (x - self._origin[0], y - self._origin[1])

    def _to_desktop(self, x: int, y: int) -> tuple[int, int]:
        """Overlay-canvas-local coordinates -> desktop coordinates."""

        return (x + self._origin[0], y + self._origin[1])

    # ---------------------------------------------------------
    # Magnifier
    # ---------------------------------------------------------

    def _update_magnifier(self, local_x: int, local_y: int) -> None:

        half = MAGNIFIER_SOURCE // 2

        left = max(0, min(self._background.width - MAGNIFIER_SOURCE, local_x - half))

        top = max(0, min(self._background.height - MAGNIFIER_SOURCE, local_y - half))

        crop = self._background.crop(
            (left, top, left + MAGNIFIER_SOURCE, top + MAGNIFIER_SOURCE)
        )

        zoomed = crop.resize(
            (MAGNIFIER_SIZE, MAGNIFIER_SIZE), Image.NEAREST
        )

        center_pixel = crop.getpixel(
            (MAGNIFIER_SOURCE // 2, MAGNIFIER_SOURCE // 2)
        )

        self._magnifier_photo = ImageTk.PhotoImage(zoomed)

        box_x, box_y = self._magnifier_position(local_x, local_y)

        self.canvas.delete("magnifier")

        self.canvas.create_image(
            box_x, box_y, anchor="nw",
            image=self._magnifier_photo, tags="magnifier",
        )

        self.canvas.create_rectangle(
            box_x, box_y, box_x + MAGNIFIER_SIZE, box_y + MAGNIFIER_SIZE,
            outline=theme.ACCENT, width=2, tags="magnifier",
        )

        mid = MAGNIFIER_SIZE // 2

        self.canvas.create_line(
            box_x + mid, box_y, box_x + mid, box_y + MAGNIFIER_SIZE,
            fill=theme.ACCENT2, tags="magnifier",
        )

        self.canvas.create_line(
            box_x, box_y + mid, box_x + MAGNIFIER_SIZE, box_y + mid,
            fill=theme.ACCENT2, tags="magnifier",
        )

        rgb_text = f"RGB {center_pixel[0]},{center_pixel[1]},{center_pixel[2]}"

        self.canvas.create_rectangle(
            box_x, box_y + MAGNIFIER_SIZE,
            box_x + MAGNIFIER_SIZE, box_y + MAGNIFIER_SIZE + 20,
            fill=theme.SURFACE, outline="", tags="magnifier",
        )

        self.canvas.create_text(
            box_x + MAGNIFIER_SIZE / 2, box_y + MAGNIFIER_SIZE + 10,
            text=rgb_text, fill=theme.TEXT,
            font=(theme.FONT_MONO, 9), tags="magnifier",
        )

    def _magnifier_position(
        self, local_x: int, local_y: int
    ) -> tuple[int, int]:

        canvas_width = int(self.canvas["width"] or self.winfo_width())

        canvas_height = int(self.canvas["height"] or self.winfo_height())

        box_x = local_x + MAGNIFIER_OFFSET

        box_y = local_y + MAGNIFIER_OFFSET

        if box_x + MAGNIFIER_SIZE > canvas_width:
            box_x = local_x - MAGNIFIER_OFFSET - MAGNIFIER_SIZE

        if box_y + MAGNIFIER_SIZE + 24 > canvas_height:
            box_y = local_y - MAGNIFIER_OFFSET - MAGNIFIER_SIZE

        return (max(0, box_x), max(0, box_y))

    def _clear_magnifier(self) -> None:

        self.canvas.delete("magnifier")

    # ---------------------------------------------------------
    # Drawing: Selection Rect + Handles
    # ---------------------------------------------------------

    def _handle_positions(self) -> dict[str, tuple[int, int]]:

        x1, y1, x2, y2 = self._rect

        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2

        return {
            "nw": (x1, y1), "n": (mid_x, y1), "ne": (x2, y1),
            "w": (x1, mid_y), "e": (x2, mid_y),
            "sw": (x1, y2), "s": (mid_x, y2), "se": (x2, y2),
        }

    def _redraw_selection(self, with_handles: bool) -> None:

        self.canvas.delete("rect", "glow", "lbl", "handle")

        x1, y1, x2, y2 = self._rect

        self.canvas.create_rectangle(
            x1 - 2, y1 - 2, x2 + 2, y2 + 2,
            outline=theme.ACCENT2, width=1, tags="glow",
        )

        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline=theme.ACCENT, width=2, tags="rect",
        )

        width, height = abs(x2 - x1), abs(y2 - y1)

        label = f"  {int(width)} x {int(height)} px  "

        label_x, label_y = min(x1, x2), min(y1, y2) - 24

        if label_y < 4:
            label_y = min(y1, y2) + 4

        label_width = len(label) * 7

        self.canvas.create_rectangle(
            label_x, label_y - 2, label_x + label_width, label_y + 16,
            fill=theme.ACCENT, outline="", tags="lbl",
        )

        self.canvas.create_text(
            label_x + 4, label_y, text=label, anchor="nw",
            fill=theme.BG, font=(theme.FONT_MONO, 10, "bold"),
            tags="lbl",
        )

        if with_handles:

            for point in self._handle_positions().values():

                hx, hy = point

                self.canvas.create_rectangle(
                    hx - HANDLE_SIZE / 2, hy - HANDLE_SIZE / 2,
                    hx + HANDLE_SIZE / 2, hy + HANDLE_SIZE / 2,
                    fill=theme.ACCENT, outline=theme.BG, tags="handle",
                )

            self.canvas.create_text(
                (x1 + x2) / 2, y2 + 20,
                text="Enter to confirm  ·  Esc to cancel  ·  "
                     "drag handles to adjust",
                fill=theme.MUTED, font=(theme.FONT_MONO, 9),
                tags="lbl",
            )

        self.canvas.tag_raise("lbl")

        self.canvas.tag_raise("handle")

    def _handle_at(self, x: int, y: int) -> str | None:

        for name, (hx, hy) in self._handle_positions().items():

            if abs(x - hx) <= HANDLE_HIT_RADIUS and abs(y - hy) <= HANDLE_HIT_RADIUS:
                return name

        return None

    def _inside_rect(self, x: int, y: int) -> bool:

        x1, y1, x2, y2 = self._rect

        return min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2)

    # ---------------------------------------------------------
    # Mouse: Idle / Dragging (initial selection)
    # ---------------------------------------------------------

    def _on_press(self, event: tk.Event) -> None:

        if self._mode == "adjusting":

            handle = self._handle_at(event.x, event.y)

            if handle is not None:

                self._mode = "resizing"

                self._active_handle = handle

                return

            if self._inside_rect(event.x, event.y):

                self._mode = "moving"

                self._move_anchor = (event.x, event.y)

                return

            # Clicked outside the current rect: start a fresh selection.

        self._mode = "dragging"

        self._rect = [event.x, event.y, event.x, event.y]

        self.canvas.delete("hint")

    def _on_drag(self, event: tk.Event) -> None:

        if self._mode == "dragging":

            self._rect[2], self._rect[3] = event.x, event.y

            self._redraw_selection(with_handles=False)

            self._update_magnifier(event.x, event.y)

        elif self._mode == "resizing":

            self._resize_active_handle(event.x, event.y)

            self._redraw_selection(with_handles=True)

            self._update_magnifier(event.x, event.y)

        elif self._mode == "moving" and self._move_anchor is not None:

            dx = event.x - self._move_anchor[0]

            dy = event.y - self._move_anchor[1]

            self._rect = [
                self._rect[0] + dx, self._rect[1] + dy,
                self._rect[2] + dx, self._rect[3] + dy,
            ]

            self._move_anchor = (event.x, event.y)

            self._redraw_selection(with_handles=True)

    def _resize_active_handle(self, x: int, y: int) -> None:

        handle = self._active_handle

        if handle is None:
            return

        if "n" in handle:
            self._rect[1] = y

        if "s" in handle:
            self._rect[3] = y

        if "w" in handle:
            self._rect[0] = x

        if "e" in handle:
            self._rect[2] = x

    def _on_release(self, event: tk.Event) -> None:

        if self._mode == "dragging":

            x1, y1, x2, y2 = self._rect

            width, height = abs(x2 - x1), abs(y2 - y1)

            if width < MIN_SELECTION or height < MIN_SELECTION:

                self.canvas.delete("rect", "glow", "lbl")

                self._mode = "idle"

                return

            self._normalize_rect()

            self._mode = "adjusting"

            self._redraw_selection(with_handles=True)

            self._clear_magnifier()

        elif self._mode in ("resizing", "moving"):

            self._normalize_rect()

            self._mode = "adjusting"

            self._active_handle = None

            self._move_anchor = None

            self._redraw_selection(with_handles=True)

            self._clear_magnifier()

    def _on_hover(self, event: tk.Event) -> None:

        if self._mode == "dragging":
            return  # handled in _on_drag already

        if self._mode == "adjusting":

            handle = self._handle_at(event.x, event.y)

            cursor = _HANDLE_CURSORS.get(handle, "crosshair")

            if self._inside_rect(event.x, event.y) and handle is None:
                cursor = "fleur"

            self.canvas.config(cursor=cursor)

    def _normalize_rect(self) -> None:

        x1, y1, x2, y2 = self._rect

        self._rect = [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]

    # ---------------------------------------------------------
    # Confirm / Cancel
    # ---------------------------------------------------------

    def _confirm(self) -> None:

        if self._mode != "adjusting":
            return

        x1, y1, x2, y2 = (int(v) for v in self._rect)

        dx1, dy1 = self._to_desktop(x1, y1)

        dx2, dy2 = self._to_desktop(x2, y2)

        self.destroy()

        self.on_selected(dx1, dy1, dx2, dy2)

    def _cancel(self) -> None:

        self.destroy()

        self.on_selected(None, None, None, None)


_HANDLE_CURSORS = {
    "nw": "top_left_corner", "se": "bottom_right_corner",
    "ne": "top_right_corner", "sw": "bottom_left_corner",
    "n": "top_side", "s": "bottom_side",
    "w": "left_side", "e": "right_side",
    None: "crosshair",
}
