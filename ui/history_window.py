"""
ScrollSnap
==========

History Window (UI)

Browses recent captures: shows a thumbnail, title, dimensions,
and timestamp for each entry, with buttons to reopen it in the
preview or remove it from history.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageTk

from controllers.history_controller import HistoryController
from storage.thumbnails import ThumbnailStorage
from ui import theme


class HistoryWindowUI(tk.Toplevel):
    """
    Lists recent captures for browsing / reopening.
    """

    def __init__(
        self,
        master: tk.Misc,
        controller: HistoryController,
        on_open,
    ) -> None:

        super().__init__(master)

        self.controller = controller

        self.on_open = on_open

        self._thumbnails = ThumbnailStorage()

        self._photo_refs: list[ImageTk.PhotoImage] = []

        self.title("ScrollSnap - History")

        theme.apply_window_theme(self)

        self.geometry("420x560")

        self._build_layout()

        self._refresh()

    def _build_layout(self) -> None:

        header = tk.Frame(self, bg=theme.BG)

        header.pack(fill=tk.X, padx=12, pady=12)

        tk.Label(
            header, text="Recent Captures", bg=theme.BG,
            fg=theme.ACCENT, font=(theme.FONT_FAMILY, 14, "bold"),
        ).pack(side=tk.LEFT)

        tk.Button(
            header, text="Clear All", command=self._clear_all,
            **theme.DANGER_BUTTON_STYLE,
        ).pack(side=tk.RIGHT)

        container = tk.Frame(self, bg=theme.BG)

        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        canvas = tk.Canvas(container, bg=theme.BG, highlightthickness=0)

        scrollbar = tk.Scrollbar(
            container, orient="vertical", command=canvas.yview
        )

        self.list_frame = tk.Frame(canvas, bg=theme.BG)

        self.list_frame.bind(
            "<Configure>",
            lambda _e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.create_window((0, 0), window=self.list_frame, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _refresh(self) -> None:

        for widget in self.list_frame.winfo_children():
            widget.destroy()

        self._photo_refs.clear()

        entries = self.controller.recent_entries()

        if not entries:

            tk.Label(
                self.list_frame, text="No captures yet.",
                bg=theme.BG, fg=theme.MUTED,
                font=(theme.FONT_FAMILY, 10),
            ).pack(pady=20)

            return

        for entry in entries:
            self._add_row(entry)

    def _add_row(self, entry) -> None:

        row = tk.Frame(self.list_frame, bg=theme.SURFACE)

        row.pack(fill=tk.X, pady=4)

        thumbnail = self._thumbnails.load(entry.id)

        if thumbnail is not None:

            photo = ImageTk.PhotoImage(thumbnail)

            self._photo_refs.append(photo)

            tk.Label(
                row, image=photo, bg=theme.SURFACE
            ).pack(side=tk.LEFT, padx=8, pady=8)

        info = tk.Frame(row, bg=theme.SURFACE)

        info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=8)

        tk.Label(
            info, text=entry.title, bg=theme.SURFACE, fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 10, "bold"), anchor="w",
        ).pack(fill=tk.X)

        tk.Label(
            info,
            text=(
                f"{entry.width} x {entry.height} px  "
                f"·  {entry.frame_count} frame(s)"
            ),
            bg=theme.SURFACE, fg=theme.MUTED,
            font=(theme.FONT_FAMILY, 9), anchor="w",
        ).pack(fill=tk.X)

        tk.Label(
            info, text=entry.created_at.split("T")[0],
            bg=theme.SURFACE, fg=theme.MUTED,
            font=(theme.FONT_FAMILY, 8), anchor="w",
        ).pack(fill=tk.X)

        actions = tk.Frame(row, bg=theme.SURFACE)

        actions.pack(side=tk.RIGHT, padx=8)

        tk.Button(
            actions, text="Open",
            command=lambda: self._open(entry),
            **theme.ACCENT_BUTTON_STYLE,
        ).pack(pady=2, fill=tk.X)

        tk.Button(
            actions, text="Delete",
            command=lambda: self._delete(entry),
            **theme.BUTTON_STYLE,
        ).pack(pady=2, fill=tk.X)

    def _open(self, entry) -> None:

        if entry.export_path:

            try:
                full_image = Image.open(entry.export_path).convert("RGB")

                self.on_open(full_image)

                return

            except (FileNotFoundError, OSError):
                pass

        thumbnail = self._thumbnails.load(entry.id)

        if thumbnail is None:
            messagebox.showerror(
                "Not Available",
                "This capture's image is no longer available.",
            )
            return

        messagebox.showinfo(
            "Thumbnail Only",
            "The original file isn't available - reopening a "
            "lower-resolution thumbnail instead.",
        )

        self.on_open(thumbnail.convert("RGB"))

    def _delete(self, entry) -> None:

        self.controller.remove_entry(entry.id)

        self._refresh()

    def _clear_all(self) -> None:

        if messagebox.askyesno(
            "Clear History", "Remove all history entries?"
        ):
            self.controller.clear_history()

            self._refresh()
