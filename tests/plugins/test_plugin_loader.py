"""
Tests for the plugin architecture: discovery, activation via the
event bus, and teardown.
"""

from __future__ import annotations

from core.event_bus import EventBus
from plugins.api import PluginContext
from plugins.plugin_loader import PluginLoader
from settings import AppConfig


def make_context(bus, notifications, clipboard):

    return PluginContext(
        event_bus=bus,
        config=AppConfig(),
        notify=lambda title, msg: notifications.append((title, msg)),
        copy_text_to_clipboard=clipboard.append,
    )


class TestPluginDiscovery:

    def test_discovers_all_builtin_plugins(self):

        loader = PluginLoader()

        classes = loader.discover_builtin_classes()

        names = {c.__name__ for c in classes}

        assert "ActivityLoggerPlugin" in names

        assert "ClipboardExportPlugin" in names

        assert "OCRSummaryPlugin" in names


class TestPluginLifecycle:

    def test_load_builtins_activates_every_plugin(self):

        bus = EventBus()

        loader = PluginLoader()

        plugins = loader.load_builtins(
            make_context(bus, [], [])
        )

        assert len(plugins) >= 3

        assert loader.active_plugins == plugins

    def test_unload_all_clears_active_list(self):

        bus = EventBus()

        loader = PluginLoader()

        loader.load_builtins(make_context(bus, [], []))

        loader.unload_all()

        assert loader.active_plugins == []


class TestClipboardExportPlugin:

    def test_copies_path_when_enabled_in_config(self):

        bus = EventBus()

        clipboard: list[str] = []

        notifications: list = []

        context = make_context(bus, notifications, clipboard)

        context.config.export.copy_to_clipboard = True

        loader = PluginLoader()

        loader.load_builtins(context)

        bus.publish("export.completed", "/tmp/output.png")

        assert clipboard == ["/tmp/output.png"]

        loader.unload_all()

    def test_does_not_copy_when_disabled(self):

        bus = EventBus()

        clipboard: list[str] = []

        context = make_context(bus, [], clipboard)

        context.config.export.copy_to_clipboard = False

        loader = PluginLoader()

        loader.load_builtins(context)

        bus.publish("export.completed", "/tmp/output.png")

        assert clipboard == []

        loader.unload_all()


class TestOCRSummaryPlugin:

    def test_low_confidence_triggers_notification(self):

        from ocr.text_extractor import TextExtractionResult

        bus = EventBus()

        notifications: list = []

        context = make_context(bus, notifications, [])

        loader = PluginLoader()

        loader.load_builtins(context)

        bus.publish(
            "ocr.extracted",
            TextExtractionResult(
                text="x", confidence=10.0, word_count=1, language="eng"
            ),
        )

        assert any(
            "Low-Confidence" in title for title, _ in notifications
        )

        loader.unload_all()

    def test_high_confidence_does_not_notify(self):

        from ocr.text_extractor import TextExtractionResult

        bus = EventBus()

        notifications: list = []

        context = make_context(bus, notifications, [])

        loader = PluginLoader()

        loader.load_builtins(context)

        bus.publish(
            "ocr.extracted",
            TextExtractionResult(
                text="x", confidence=99.0, word_count=1, language="eng"
            ),
        )

        assert notifications == []

        loader.unload_all()
