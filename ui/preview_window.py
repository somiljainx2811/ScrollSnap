"""
ScrollSnap
==========

Preview Window (UI)

The Tkinter dialog for the "preview before save" workflow:
shows the captured/stitched image, lets the user crop, rotate,
flip, annotate, cut out a shape, and finally export.

This is the UI wiring layer only - all real logic lives in
`controllers.preview_controller.PreviewController` and the
`preview.preview_window.PreviewWindow` state machine it wraps.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, simpledialog
from tkinter import ttk

from PIL import Image, ImageTk

from controllers.export_controller import ExportController
from controllers.ocr_controller import OCRController
from controllers.preview_controller import PreviewController
from models.rectangle import Rectangle
from preview.annotations import Annotation, AnnotationType
from preview.preview_window import PreviewState
from shapes.circle import CircleShape
from shapes.ellipse import EllipseShape
from shapes.rectangle import RectangleShape
from shapes.rounded_rectangle import RoundedRectangleShape
from shapes.star import StarShape
from ui import theme


MAX_DISPLAY_SIZE = (900, 620)

_SHAPE_FACTORIES = {
    "Rectangle": lambda w, h: RectangleShape(0, 0, w, h),
    "Rounded Rectangle": lambda w, h: RoundedRectangleShape(
        0, 0, w, h, min(w, h) * 0.12
    ),
    "Circle": lambda w, h: CircleShape(
        w / 2 - min(w, h) / 2, h / 2 - min(w, h) / 2, min(w, h) / 2
    ),
    "Ellipse": lambda w, h: EllipseShape(0, 0, w, h),
    "Star": lambda w, h: StarShape(
        center_x=w / 2, center_y=h / 2,
        outer_radius=min(w, h) / 2, inner_radius=min(w, h) / 4,
        points=5,
    ),
}

_ANNOTATION_TOOLS = {
    "Arrow": AnnotationType.ARROW,
    "Rectangle": AnnotationType.RECTANGLE,
    "Ellipse": AnnotationType.ELLIPSE,
    "Highlight": AnnotationType.HIGHLIGHT,
    "Blur": AnnotationType.BLUR,
    "Pixelate": AnnotationType.PIXELATE,
    "Text": AnnotationType.TEXT,
    "Freehand": AnnotationType.FREEHAND,
}

_COLOR_SWATCHES = ["#FF3B30", "#00E5FF", "#FFB800", "#00FF88", "#FFFFFF"]


class PreviewWindowUI(tk.Toplevel):
    """
    Interactive preview / edit / annotate / export dialog.
    """

    def __init__(
        self,
        master: tk.Misc,
        controller: PreviewController,
        on_close=None,
    ) -> None:

        super().__init__(master)

        self.controller = controller

        self.exporter = ExportController()

        self.ocr = OCRController()

        self.on_close_callback = on_close

        self.title("ScrollSnap - Preview")

        theme.apply_window_theme(self)

        self.geometry("1000x760")

        self._scale = 1.0

        self._photo: ImageTk.PhotoImage | None = None

        self._active_tool: str | None = None

        self._selected_color = _COLOR_SWATCHES[0]

        self._drag_start: tuple[int, int] | None = None

        self._crop_mode = False

        self._crop_rect_id: int | None = None

        self._shape_var = tk.StringVar(value="Rectangle")

        self._build_layout()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.refresh()

    # ---------------------------------------------------------
    # Layout
    # ---------------------------------------------------------

    def _build_layout(self) -> None:

        toolbar = tk.Frame(self, bg=theme.SURFACE)

        toolbar.pack(fill=tk.X, side=tk.TOP)

        self._add_button(toolbar, "Rotate ⟲", self._rotate_ccw)
        self._add_button(toolbar, "Rotate ⟳", self._rotate_cw)
        self._add_button(toolbar, "Flip H", self._flip_h)
        self._add_button(toolbar, "Flip V", self._flip_v)
        self._add_button(toolbar, "Crop", self._toggle_crop_mode)
        self._add_button(toolbar, "Undo", self._undo)
        self._add_button(toolbar, "Redo", self._redo)
        self._add_button(toolbar, "Extract Text", self._extract_text)

        canvas_frame = tk.Frame(self, bg=theme.BG)

        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            canvas_frame,
            bg=theme.SURFACE,
            highlightthickness=0,
        )

        self.canvas.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        self.canvas.bind("<ButtonPress-1>", self._on_canvas_press)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

        annotate_bar = tk.Frame(self, bg=theme.SURFACE2)

        annotate_bar.pack(fill=tk.X, side=tk.TOP)

        tk.Label(
            annotate_bar, text="Annotate:", bg=theme.SURFACE2,
            fg=theme.MUTED, font=(theme.FONT_FAMILY, 9, "bold"),
        ).pack(side=tk.LEFT, padx=(10, 4))

        for name in _ANNOTATION_TOOLS:
            self._add_tool_button(annotate_bar, name)

        for color in _COLOR_SWATCHES:
            self._add_color_swatch(annotate_bar, color)

        bottom_bar = tk.Frame(self, bg=theme.SURFACE)

        bottom_bar.pack(fill=tk.X, side=tk.BOTTOM)

        tk.Label(
            bottom_bar, text="Shape cutout:", bg=theme.SURFACE,
            fg=theme.MUTED, font=(theme.FONT_FAMILY, 9, "bold"),
        ).pack(side=tk.LEFT, padx=(10, 4))

        shape_menu = ttk.Combobox(
            bottom_bar,
            textvariable=self._shape_var,
            values=list(_SHAPE_FACTORIES.keys()),
            state="readonly",
            width=18,
        )

        shape_menu.pack(side=tk.LEFT, padx=4, pady=6)

        self._add_button(
            bottom_bar, "Apply Shape", self._apply_shape_cutout
        )

        tk.Frame(bottom_bar, bg=theme.SURFACE, width=1).pack(
            side=tk.LEFT, expand=True, fill=tk.X
        )

        self._add_button(
            bottom_bar, "Export...", self._export,
            style=theme.ACCENT_BUTTON_STYLE,
        )

    def _add_button(self, parent, text, command, style=None) -> tk.Button:

        button = tk.Button(
            parent, text=text, command=command,
            **(style or theme.BUTTON_STYLE),
        )

        button.pack(side=tk.LEFT, padx=4, pady=6)

        return button

    def _add_tool_button(self, parent, name: str) -> None:

        def _select():
            self._active_tool = name
            self._set_mode(PreviewState.ANNOTATING)

        self._add_button(parent, name, _select)

    def _add_color_swatch(self, parent, color: str) -> None:

        def _select():
            self._selected_color = color

        swatch = tk.Button(
            parent, bg=color, activebackground=color,
            width=2, relief="flat", command=_select,
        )

        swatch.pack(side=tk.LEFT, padx=2, pady=6)

    # ---------------------------------------------------------
    # Rendering
    # ---------------------------------------------------------

    def refresh(self) -> None:

        image = self.controller.render_current()

        display_image, self._scale = self._fit_to_display(image)

        self._photo = ImageTk.PhotoImage(display_image)

        self.canvas.delete("preview")

        self.canvas.config(
            width=display_image.width, height=display_image.height
        )

        self.canvas.create_image(
            0, 0, anchor="nw", image=self._photo, tags="preview"
        )

    def _fit_to_display(
        self, image: Image.Image
    ) -> tuple[Image.Image, float]:

        max_w, max_h = MAX_DISPLAY_SIZE

        scale = min(max_w / image.width, max_h / image.height, 1.0)

        if scale >= 1.0:
            return image, 1.0

        new_size = (
            max(1, int(image.width * scale)),
            max(1, int(image.height * scale)),
        )

        return image.resize(new_size, Image.LANCZOS), scale

    def _to_image_coords(self, x: int, y: int) -> tuple[float, float]:

        return (x / self._scale, y / self._scale)

    # ---------------------------------------------------------
    # Mode Management
    # ---------------------------------------------------------

    def _set_mode(self, target: PreviewState) -> None:

        window = self.controller.window

        if window.state == target:
            return

        if target == PreviewState.EDITING:
            window.enter_editing()

        elif target == PreviewState.ANNOTATING:
            window.enter_annotating()

        elif target == PreviewState.VIEWING:
            window.return_to_viewing()

    # ---------------------------------------------------------
    # Edit Actions
    # ---------------------------------------------------------

    def _rotate_ccw(self) -> None:
        self._set_mode(PreviewState.EDITING)
        self.controller.window.rotate(-90)
        self.refresh()

    def _rotate_cw(self) -> None:
        self._set_mode(PreviewState.EDITING)
        self.controller.window.rotate(90)
        self.refresh()

    def _flip_h(self) -> None:
        self._set_mode(PreviewState.EDITING)
        self.controller.window.flip_horizontal()
        self.refresh()

    def _flip_v(self) -> None:
        self._set_mode(PreviewState.EDITING)
        self.controller.window.flip_vertical()
        self.refresh()

    def _undo(self) -> None:
        if self.controller.window.undo():
            self.refresh()

    def _redo(self) -> None:
        if self.controller.window.redo():
            self.refresh()

    def _toggle_crop_mode(self) -> None:

        self._crop_mode = not self._crop_mode

        self._active_tool = None

        if self._crop_mode:
            self._set_mode(PreviewState.EDITING)

    def _apply_shape_cutout(self) -> None:

        image = self.controller.render_current()

        factory = _SHAPE_FACTORIES[self._shape_var.get()]

        shape = factory(image.width, image.height)

        try:
            cutout = self.controller.apply_shape_cutout(shape)

        except Exception as exc:
            messagebox.showerror("Shape Cutout Failed", str(exc))
            return

        self._last_cutout = cutout

        self._show_cutout_preview(cutout)

    def _show_cutout_preview(self, cutout: Image.Image) -> None:

        display_image, _ = self._fit_to_display(cutout)

        self._photo = ImageTk.PhotoImage(display_image)

        self.canvas.delete("preview")

        self.canvas.config(
            width=display_image.width, height=display_image.height
        )

        self.canvas.create_image(
            0, 0, anchor="nw", image=self._photo, tags="preview"
        )

    # ---------------------------------------------------------
    # Canvas Interaction (crop + annotations)
    # ---------------------------------------------------------

    def _on_canvas_press(self, event: tk.Event) -> None:

        self._drag_start = (event.x, event.y)

    def _on_canvas_drag(self, event: tk.Event) -> None:

        if self._drag_start is None:
            return

        self.canvas.delete("draft")

        sx, sy = self._drag_start

        if self._active_tool in ("Arrow", "Freehand"):

            self.canvas.create_line(
                sx, sy, event.x, event.y,
                fill=self._selected_color, width=3, tags="draft",
            )

        else:

            self.canvas.create_rectangle(
                sx, sy, event.x, event.y,
                outline=self._selected_color, width=2, tags="draft",
            )

    def _on_canvas_release(self, event: tk.Event) -> None:

        if self._drag_start is None:
            return

        sx, sy = self._drag_start

        self._drag_start = None

        self.canvas.delete("draft")

        if abs(event.x - sx) < 3 and abs(event.y - sy) < 3:
            return

        start_image = self._to_image_coords(sx, sy)

        end_image = self._to_image_coords(event.x, event.y)

        if self._crop_mode:

            self._apply_crop(start_image, end_image)

        elif self._active_tool is not None:

            self._add_annotation(start_image, end_image)

    def _apply_crop(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
    ) -> None:

        rect = Rectangle(
            min(start[0], end[0]), min(start[1], end[1]),
            max(start[0], end[0]), max(start[1], end[1]),
        )

        self._set_mode(PreviewState.EDITING)

        try:
            self.controller.window.crop(rect)

        except Exception as exc:
            messagebox.showerror("Crop Failed", str(exc))
            return

        self._crop_mode = False

        self.refresh()

    def _add_annotation(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
    ) -> None:

        tool = self._active_tool

        annotation_type = _ANNOTATION_TOOLS[tool]

        self._set_mode(PreviewState.ANNOTATING)

        if annotation_type == AnnotationType.TEXT:

            text = simpledialog.askstring(
                "Add Text", "Text:", parent=self
            )

            if not text:
                return

            annotation = Annotation(
                AnnotationType.TEXT,
                points=[start],
                text=text,
                color=self._selected_color,
                font_size=24.0,
            )

        else:

            annotation = Annotation(
                annotation_type,
                points=[start, end],
                color=self._selected_color,
                stroke_width=3.0,
            )

        self.controller.window.annotations.add(annotation)

        self.refresh()

    # ---------------------------------------------------------
    # OCR
    # ---------------------------------------------------------

    def _extract_text(self) -> None:

        image = self.controller.render_current()

        self.config(cursor="watch")

        self.update_idletasks()

        try:
            result = self.ocr.extract_text(image)

        except Exception as exc:
            messagebox.showerror("OCR Failed", str(exc))
            return

        finally:
            self.config(cursor="")

        if result.is_empty:
            messagebox.showinfo(
                "No Text Found",
                "Tesseract didn't recognize any text in this image.",
            )
            return

        self._show_ocr_dialog(result.text, image)

    def _show_ocr_dialog(self, text: str, image: Image.Image) -> None:

        dialog = tk.Toplevel(self)

        dialog.title("Extracted Text")

        theme.apply_window_theme(dialog)

        dialog.geometry("480x420")

        text_widget = tk.Text(
            dialog, wrap="word", bg=theme.SURFACE, fg=theme.TEXT,
            insertbackground=theme.TEXT, relief="flat",
            font=(theme.FONT_FAMILY, 10),
        )

        text_widget.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        text_widget.insert("1.0", text)

        button_row = tk.Frame(dialog, bg=theme.BG)

        button_row.pack(fill=tk.X, padx=12, pady=(0, 12))

        def _copy():
            self.clipboard_clear()
            self.clipboard_append(text_widget.get("1.0", "end-1c"))

        def _save_markdown():

            path = filedialog.asksaveasfilename(
                defaultextension=".md",
                filetypes=[("Markdown", "*.md")],
            )

            if not path:
                return

            written = self.ocr.export_markdown(
                text_widget.get("1.0", "end-1c"), path
            )

            messagebox.showinfo("Saved", f"Saved to:\n{written}")

        def _save_pdf():

            path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Searchable PDF", "*.pdf")],
            )

            if not path:
                return

            written = self.ocr.export_searchable_pdf(image, path)

            messagebox.showinfo("Saved", f"Saved to:\n{written}")

        tk.Button(
            button_row, text="Copy", command=_copy,
            **theme.BUTTON_STYLE,
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            button_row, text="Save as .md", command=_save_markdown,
            **theme.BUTTON_STYLE,
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            button_row, text="Save as Searchable PDF",
            command=_save_pdf, **theme.ACCENT_BUTTON_STYLE,
        ).pack(side=tk.LEFT, padx=2)

    # ---------------------------------------------------------
    # Export
    # ---------------------------------------------------------

    def _export(self) -> None:

        path = filedialog.asksaveasfilename(
            title="Export Image",
            defaultextension=".png",
            filetypes=[
                ("PNG", "*.png"),
                ("JPEG", "*.jpg"),
                ("WEBP", "*.webp"),
                ("TIFF", "*.tiff"),
            ],
        )

        if not path:
            return

        try:

            final_image = self.controller.render_for_export()

            written = self.exporter.export(final_image, path)

        except Exception as exc:
            messagebox.showerror("Export Failed", str(exc))
            return

        messagebox.showinfo(
            "Export Complete", f"Saved to:\n{written}"
        )

    def _on_close(self) -> None:

        if self.on_close_callback is not None:
            self.on_close_callback()

        self.destroy()
