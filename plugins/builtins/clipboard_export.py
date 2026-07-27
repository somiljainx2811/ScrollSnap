"""
ScrollSnap
==========

Clipboard Export Plugin

When `config.export.copy_to_clipboard` is enabled, copies the
path of every exported file to the clipboard and shows a
notification confirming the export.
"""

from __future__ import annotations

from plugins.api import Plugin, PluginContext


class ClipboardExportPlugin(Plugin):

    name = "Clipboard Export"

    version = "1.0.0"

    description = (
        "Copies exported file paths to the clipboard and shows "
        "a confirmation notification."
    )

    def activate(self, context: PluginContext) -> None:

        self._context = context

        self._subscribe(context, "export.completed", self._on_export_completed)

    def _on_export_completed(self, event) -> None:

        path = event.data

        if not self._context.config.export.copy_to_clipboard:
            return

        self._context.copy_text_to_clipboard(str(path))

        self._context.notify(
            "Copied to Clipboard", f"File path copied:\n{path}"
        )
