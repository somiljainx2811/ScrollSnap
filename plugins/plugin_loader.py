"""
ScrollSnap
==========

Plugin Loader

Discovers `Plugin` subclasses in `plugins/builtins/` and
activates/deactivates them.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil

from plugins import builtins
from plugins.api import Plugin, PluginContext


class PluginLoader:
    """
    Loads and manages the lifecycle of builtin plugins.
    """

    def __init__(self) -> None:

        self._active: list[Plugin] = []

    @property
    def active_plugins(self) -> list[Plugin]:
        return list(self._active)

    def discover_builtin_classes(self) -> list[type[Plugin]]:
        """
        Import every module in `plugins.builtins` and collect any
        `Plugin` subclasses defined there.
        """

        classes: list[type[Plugin]] = []

        for module_info in pkgutil.iter_modules(builtins.__path__):

            module = importlib.import_module(
                f"plugins.builtins.{module_info.name}"
            )

            for _, obj in inspect.getmembers(module, inspect.isclass):

                if (
                    issubclass(obj, Plugin)
                    and obj is not Plugin
                    and obj.__module__ == module.__name__
                ):
                    classes.append(obj)

        return classes

    def load_builtins(self, context: PluginContext) -> list[Plugin]:
        """
        Discover, instantiate, and activate every builtin plugin.
        """

        for plugin_class in self.discover_builtin_classes():

            plugin = plugin_class()

            plugin.activate(context)

            self._active.append(plugin)

        return self._active

    def unload_all(self) -> None:

        for plugin in self._active:
            plugin.deactivate()

        self._active.clear()

    def __repr__(self) -> str:

        names = [p.name for p in self._active]

        return f"PluginLoader(active={names})"
