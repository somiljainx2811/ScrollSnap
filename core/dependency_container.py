"""
ScrollSnap Dependency Injection Container
=========================================

A lightweight dependency injection container used to manage
application-wide singleton services and factories.

Responsibilities
----------------
- Register singleton instances
- Register factories
- Resolve dependencies
- Centralize object creation
"""

from __future__ import annotations

from typing import Any, Callable


class DependencyContainer:
    """
    Simple dependency injection container.
    """

    def __init__(self) -> None:

        self._singletons: dict[type, Any] = {}

        self._factories: dict[type, Callable[[], Any]] = {}

    # --------------------------------------------------

    def register_singleton(
        self,
        interface: type,
        instance: Any,
    ) -> None:
        """
        Register an already-created singleton instance.
        """

        self._singletons[interface] = instance

    # --------------------------------------------------

    def register_factory(
        self,
        interface: type,
        factory: Callable[[], Any],
    ) -> None:
        """
        Register a factory used to lazily construct objects.
        """

        self._factories[interface] = factory

    # --------------------------------------------------

    def resolve(
        self,
        interface: type,
    ) -> Any:
        """
        Resolve an object.
        """

        if interface in self._singletons:
            return self._singletons[interface]

        if interface in self._factories:

            instance = self._factories[interface]()

            return instance

        raise KeyError(
            f"{interface.__name__} is not registered."
        )

    # --------------------------------------------------

    def contains(
        self,
        interface: type,
    ) -> bool:

        return (
            interface in self._singletons
            or interface in self._factories
        )

    # --------------------------------------------------

    def remove(
        self,
        interface: type,
    ) -> None:

        self._singletons.pop(interface, None)

        self._factories.pop(interface, None)

    # --------------------------------------------------

    def clear(self) -> None:

        self._singletons.clear()

        self._factories.clear()


# ----------------------------------------------------------
# Global Application Container
# ----------------------------------------------------------

container = DependencyContainer()