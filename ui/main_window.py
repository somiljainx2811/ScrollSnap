"""
ScrollSnap
==========

Main Window (UI)

The application's root window: region selection, single
screenshots, and scrolling capture sessions. Successful captures
open `ui.preview_window.PreviewWindowUI` automatically.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from capture.auto_scroll.scroll_strategies import ScrollDirection
from controllers.capture_controller import CaptureController
from controllers.history_controller import HistoryController
from controllers.preview_controller import PreviewController
from controllers.stitch_controller import StitchController
from core.application import app
from core.event_bus import event_bus
from models.rectangle import Rectangle
from plugins.api import PluginContext
from plugins.plugin_loader import PluginLoader
from ui import theme
from ui.history_window import HistoryWindowUI
from ui.preview_window import PreviewWindowUI
from ui.region_indicator import RegionIndicator
from ui.selection_overlay import SelectionOverlay
from version import VERSION_STRING


class MainWindow(tk.Tk):
    """
    Root ScrollSnap application window.
    """

    def __init__(self) -> None:

        super().__init__()

        self.title(f"ScrollSnap {VERSION_STRING}")

        theme.apply_window_theme(self)

        self.geometry("420x460")

        self.resizable(False, False)

        self.capture_controller = CaptureController()

        self.stitch_controller = StitchController()

        self.history_controller = HistoryController()

        self.capture_controller.add_frame_listener(
            self._on_frame_for_recovery
        )

        self.region_indicator = RegionIndicator(self)

        event_bus.subscribe("capture.error", self._on_capture_error_event)

        event_bus.subscribe(
            "capture.frame_captured", self._on_frame_captured_event
        )

        self._preview_windows: list[PreviewWindowUI] = []

        self._is_capturing = False

        self._build_layout()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.after(200, self._check_recovery)

        self.plugin_loader = PluginLoader()

        self.plugin_loader.load_builtins(
            PluginContext(
                event_bus=event_bus,
                config=app.config,
                notify=self._notify,
                copy_text_to_clipboard=self._copy_text_to_clipboard,
            )
        )

    def report_callback_exception(self, exc, val, tb) -> None:
        """
        Tkinter calls this whenever a widget callback (button
        command, key binding, etc.) raises. The default
        implementation just prints a traceback to stderr - which,
        in a windowed build with no console attached, means the
        error is completely invisible and it looks like the
        button did nothing at all. Show it to the user instead.
        """

        import traceback

        traceback.print_exception(exc, val, tb)

        messagebox.showerror("ScrollSnap Error", str(val) or str(exc))

    # ---------------------------------------------------------
    # Layout
    # ---------------------------------------------------------

    def _build_layout(self) -> None:

        header = tk.Frame(self, bg=theme.BG)

        header.pack(fill=tk.X, padx=16, pady=(16, 8))

        tk.Label(
            header, text="ScrollSnap", bg=theme.BG, fg=theme.ACCENT,
            font=(theme.FONT_FAMILY, 20, "bold"),
        ).pack(anchor="w")

        tk.Label(
            header, text="Scrolling screenshot capture",
            bg=theme.BG, fg=theme.MUTED,
            font=(theme.FONT_FAMILY, 10),
        ).pack(anchor="w")

        region_frame = tk.LabelFrame(
            self, text="Region", bg=theme.SURFACE, fg=theme.TEXT,
            bd=0, font=(theme.FONT_FAMILY, 9, "bold"),
        )

        region_frame.pack(fill=tk.X, padx=16, pady=8)

        self.region_label = tk.Label(
            region_frame, text="No region selected", bg=theme.SURFACE,
            fg=theme.MUTED, font=(theme.FONT_FAMILY, 10), anchor="w",
        )

        self.region_label.pack(fill=tk.X, padx=10, pady=(4, 8))

        tk.Button(
            region_frame, text="Select Region",
            command=self._select_region, **theme.ACCENT_BUTTON_STYLE,
        ).pack(padx=10, pady=(0, 10), anchor="w")

        options_frame = tk.LabelFrame(
            self, text="Scrolling Capture Options", bg=theme.SURFACE,
            fg=theme.TEXT, bd=0, font=(theme.FONT_FAMILY, 9, "bold"),
        )

        options_frame.pack(fill=tk.X, padx=16, pady=8)

        row1 = tk.Frame(options_frame, bg=theme.SURFACE)

        row1.pack(fill=tk.X, padx=10, pady=4)

        tk.Label(
            row1, text="Interval (s):", bg=theme.SURFACE, fg=theme.TEXT,
        ).pack(side=tk.LEFT)

        self.interval_var = tk.DoubleVar(value=0.5)

        tk.Spinbox(
            row1, from_=0.1, to=5.0, increment=0.1, width=6,
            textvariable=self.interval_var,
        ).pack(side=tk.LEFT, padx=8)

        self.auto_scroll_var = tk.BooleanVar(value=False)

        tk.Checkbutton(
            row1, text="Auto-scroll for me",
            variable=self.auto_scroll_var, bg=theme.SURFACE,
            fg=theme.TEXT, selectcolor=theme.SURFACE2,
            activebackground=theme.SURFACE,
        ).pack(side=tk.LEFT, padx=8)

        self.smart_timing_var = tk.BooleanVar(value=True)

        tk.Checkbutton(
            row1, text="Smart timing",
            variable=self.smart_timing_var, bg=theme.SURFACE,
            fg=theme.TEXT, selectcolor=theme.SURFACE2,
            activebackground=theme.SURFACE,
        ).pack(side=tk.LEFT, padx=8)

        row2 = tk.Frame(options_frame, bg=theme.SURFACE)

        row2.pack(fill=tk.X, padx=10, pady=(4, 10))

        tk.Label(
            row2, text="Direction:", bg=theme.SURFACE, fg=theme.TEXT,
        ).pack(side=tk.LEFT)

        self.direction_var = tk.StringVar(value="DOWN")

        ttk.Combobox(
            row2, textvariable=self.direction_var,
            values=["DOWN", "UP", "LEFT", "RIGHT"],
            state="readonly", width=8,
        ).pack(side=tk.LEFT, padx=8)

        tk.Label(
            row2, text="Strategy:", bg=theme.SURFACE, fg=theme.TEXT,
        ).pack(side=tk.LEFT, padx=(12, 0))

        self.strategy_var = tk.StringVar(value="Mouse Wheel")

        ttk.Combobox(
            row2, textvariable=self.strategy_var,
            values=self.capture_controller.available_scroll_strategies(),
            state="readonly", width=12,
        ).pack(side=tk.LEFT, padx=8)

        actions = tk.Frame(self, bg=theme.BG)

        actions.pack(fill=tk.X, padx=16, pady=12)

        tk.Button(
            actions, text="Snap Screenshot", command=self._snap,
            **theme.BUTTON_STYLE,
        ).pack(fill=tk.X, pady=4)

        self.capture_button = tk.Button(
            actions, text="Start Scrolling Capture",
            command=self._toggle_capture, **theme.ACCENT_BUTTON_STYLE,
        )

        self.capture_button.pack(fill=tk.X, pady=4)

        tk.Button(
            actions, text="History", command=self._open_history,
            **theme.BUTTON_STYLE,
        ).pack(fill=tk.X, pady=4)

        self.status_var = tk.StringVar(value="Ready.")

        tk.Label(
            self, textvariable=self.status_var, bg=theme.BG,
            fg=theme.MUTED, font=(theme.FONT_FAMILY, 9), anchor="w",
            wraplength=380, justify="left",
        ).pack(fill=tk.X, padx=16, pady=(0, 12))

    # ---------------------------------------------------------
    # Crash Recovery
    # ---------------------------------------------------------

    def _check_recovery(self) -> None:

        if not self.history_controller.has_pending_recovery():
            return

        session = self.history_controller.recover_session()

        if session is None or session.is_empty:
            self.history_controller.discard_recovery()
            return

        restore = messagebox.askyesno(
            "Restore Previous Session?",
            f"ScrollSnap didn't close cleanly last time. "
            f"A capture with {session.frame_count} frame(s) can "
            f"be restored. Restore it now?",
        )

        if restore:

            self.status_var.set(
                f"Restored {session.frame_count} frame(s) from "
                "the previous session."
            )

            if session.frame_count == 1:
                self._open_preview(session.frames[0].image)

            else:
                result = self.stitch_controller.stitch(session.frames)

                if result.success:
                    self._open_preview(result.image)

            self.history_controller.discard_recovery()

        else:

            self.history_controller.discard_recovery()

    def _on_frame_for_recovery(self, frame) -> None:

        if self._is_capturing:
            self.history_controller.track_frame(frame)

    def _on_frame_captured_event(self, event) -> None:
        """
        Fires once per capture tick, including while nothing on
        screen has changed. Surfacing it in the status bar is the
        only visible sign, during a run, that ScrollSnap is doing
        anything at all - without it, a capture session looks
        completely frozen until Stop is clicked.
        """

        self.after(0, self._update_capture_progress)

    def _update_capture_progress(self) -> None:

        if not self._is_capturing:
            return

        count = len(self.capture_controller.frames)

        self.status_var.set(
            f"Capturing... {count} frame"
            f"{'s' if count != 1 else ''} so far. Click Stop when finished."
        )

    # ---------------------------------------------------------
    # Capture Errors
    # ---------------------------------------------------------

    def _on_capture_error_event(self, event) -> None:
        """
        `capture.error` is published from the background capture
        thread, so hand the actual UI update to the main thread
        via `after(0, ...)` rather than touching Tkinter widgets
        directly here.
        """

        self.after(0, lambda: self._handle_capture_error(event.data))

    def _handle_capture_error(self, exc: Exception) -> None:

        self._is_capturing = False

        self.capture_button.config(text="Start Scrolling Capture")

        region = self.capture_controller.region_manager.region

        if region is not None:
            self.region_indicator.show(region.rectangle, color=theme.ACCENT)

        self.history_controller.end_session()

        self.status_var.set("Capture stopped - an error occurred.")

        messagebox.showerror("Capture Failed", str(exc) or type(exc).__name__)

    # ---------------------------------------------------------
    # History
    # ---------------------------------------------------------

    def _open_history(self) -> None:

        HistoryWindowUI(self, self.history_controller, self._open_preview)

    # ---------------------------------------------------------
    # Region Selection
    # ---------------------------------------------------------

    def _select_region(self) -> None:

        self.region_indicator.hide()

        self.withdraw()

        self.after(150, self._show_overlay)

    def _show_overlay(self) -> None:

        SelectionOverlay(self, self._on_region_selected)

    def _on_region_selected(self, x1, y1, x2, y2) -> None:

        self.deiconify()

        if x1 is None:
            self.status_var.set("Region selection cancelled.")

            existing = self.capture_controller.region_manager.region

            if existing is not None:
                self.region_indicator.show(existing.rectangle)

            return

        rectangle = Rectangle(x1, y1, x2, y2)

        self.capture_controller.select_region(rectangle)

        self.region_label.config(
            text=(
                f"{int(rectangle.width)} x {int(rectangle.height)} px  "
                f"@ ({x1}, {y1})"
            ),
            fg=theme.SUCCESS,
        )

        self.status_var.set("Region selected. Ready to capture.")

        self.region_indicator.show(rectangle)

    # ---------------------------------------------------------
    # Single Snapshot
    # ---------------------------------------------------------

    def _snap(self) -> None:

        if not self.capture_controller.region_manager.has_region:
            messagebox.showwarning(
                "No Region", "Select a capture region first."
            )
            return

        try:
            frame = self.capture_controller.snap()

        except Exception as exc:
            messagebox.showerror("Capture Failed", str(exc))
            return

        self.status_var.set("Captured single screenshot.")

        self.history_controller.record_capture(
            frame.image, title="Screenshot", frame_count=1
        )

        self._open_preview(frame.image)

    # ---------------------------------------------------------
    # Scrolling Capture
    # ---------------------------------------------------------

    def _toggle_capture(self) -> None:

        if self._is_capturing:
            self._stop_capture()

        else:
            self._start_capture()

    def _start_capture(self) -> None:

        if not self.capture_controller.region_manager.has_region:
            messagebox.showwarning(
                "No Region", "Select a capture region first."
            )
            return

        direction = ScrollDirection[self.direction_var.get()]

        self.history_controller.begin_session(
            self.capture_controller.region_manager.region
        )

        try:
            self.capture_controller.start_capture(
                interval_seconds=self.interval_var.get(),
                auto_scroll=self.auto_scroll_var.get(),
                scroll_direction=direction,
                scroll_strategy=self.strategy_var.get(),
                smart_timing=self.smart_timing_var.get(),
            )

        except Exception as exc:
            self.history_controller.end_session()
            messagebox.showerror("Capture Failed to Start", str(exc))
            self.status_var.set("Capture failed to start.")
            return

        self._is_capturing = True

        self.capture_button.config(text="Stop Capture")

        self.status_var.set("Capturing... click Stop when finished.")

        region = self.capture_controller.region_manager.region

        if region is not None:
            self.region_indicator.show(region.rectangle, color=theme.DANGER)

    def _stop_capture(self) -> None:

        self.capture_controller.stop_capture()

        self._is_capturing = False

        self.capture_button.config(text="Start Scrolling Capture")

        region = self.capture_controller.region_manager.region

        if region is not None:
            self.region_indicator.show(region.rectangle, color=theme.ACCENT)

        frames = self.capture_controller.frames

        if len(frames) == 0:

            self.status_var.set("Capture stopped - no frames captured.")

            self.history_controller.end_session()

            return

        if len(frames) == 1:

            self.status_var.set("Capture stopped - 1 frame.")

            self.history_controller.record_capture(
                frames[0].image, title="Scrolling Capture", frame_count=1
            )

            self.history_controller.end_session()

            self._open_preview(frames[0].image)

            return

        self.status_var.set(f"Stitching {len(frames)} frames...")

        self.update_idletasks()

        result = self.stitch_controller.stitch(frames)

        if not result.success:

            messagebox.showerror(
                "Stitching Failed", result.error or "Unknown error"
            )

            self.status_var.set("Stitching failed.")

            self.history_controller.end_session()

            return

        self.status_var.set(
            f"Stitched {result.frame_count} frames -> "
            f"{result.width}x{result.height}."
        )

        self.history_controller.record_capture(
            result.image,
            title="Scrolling Capture",
            frame_count=result.frame_count,
        )

        self.history_controller.end_session()

        self._open_preview(result.image)

    # ---------------------------------------------------------
    # Preview
    # ---------------------------------------------------------

    def _open_preview(self, image) -> None:

        preview_controller = PreviewController()

        preview_controller.open(image)

        window = PreviewWindowUI(
            self,
            preview_controller,
            on_close=lambda: self._forget_preview(window),
        )

        self._preview_windows.append(window)

    def _forget_preview(self, window: PreviewWindowUI) -> None:

        if window in self._preview_windows:
            self._preview_windows.remove(window)

    # ---------------------------------------------------------
    # Plugin Support
    # ---------------------------------------------------------

    def _notify(self, title: str, message: str) -> None:

        self.after(0, lambda: messagebox.showinfo(title, message))

    def _copy_text_to_clipboard(self, text: str) -> None:

        self.clipboard_clear()

        self.clipboard_append(text)

    # ---------------------------------------------------------
    # Shutdown
    # ---------------------------------------------------------

    def _on_close(self) -> None:

        if self._is_capturing:
            self.capture_controller.stop_capture()

        self.region_indicator.hide()

        event_bus.unsubscribe("capture.error", self._on_capture_error_event)

        event_bus.unsubscribe(
            "capture.frame_captured", self._on_frame_captured_event
        )

        self.plugin_loader.unload_all()

        self.capture_controller.shutdown()

        self.destroy()
