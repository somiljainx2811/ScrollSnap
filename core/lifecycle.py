"""
ScrollSnap Lifecycle Manager
============================

Coordinates startup and shutdown of application components.

Components register startup and shutdown callbacks,
which are executed in a deterministic order.

This prevents startup logic from being spread throughout
the codebase and simplifies dependency management.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class LifecycleTask:
    """
    Represents a startup/shutdown task.
    """

    name: str

    startup: Callable[[], None]

    shutdown: Callable[[], None]


class LifecycleManager:

    def __init__(self) -> None:

        self._tasks: list[LifecycleTask] = []

        self._started = False

    # -------------------------------------------------

    def register(
        self,
        task: LifecycleTask,
    ) -> None:
        """
        Register a lifecycle task.

        Registration order determines startup order.
        """

        if self._started:
            raise RuntimeError(
                "Cannot register tasks after startup."
            )

        self._tasks.append(task)

    # -------------------------------------------------

    def startup(self) -> None:
        """
        Execute startup tasks.
        """

        if self._started:
            return

        for task in self._tasks:

            task.startup()

        self._started = True

    # -------------------------------------------------

    def shutdown(self) -> None:
        """
        Execute shutdown tasks.

        Reverse registration order.
        """

        if not self._started:
            return

        for task in reversed(self._tasks):

            task.shutdown()

        self._started = False

    # -------------------------------------------------

    @property
    def started(self) -> bool:

        return self._started

    # -------------------------------------------------

    @property
    def task_count(self) -> int:

        return len(self._tasks)


lifecycle = LifecycleManager()