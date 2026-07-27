"""
ScrollSnap
==========

Preview Navigation

Manages the "current item" index when previewing a sequence of
items (captured frames, history entries, comparison pairs, etc).

Responsibilities
----------------
- Track current index
- Move forward / backward / to a specific index
- Report boundary state
- Notify listeners on change

Does NOT:
- Load or render images
- Know what the items actually are
"""

from __future__ import annotations

from typing import Callable


class NavigationController:
    """
    Controls the current index within a bounded sequence.
    """

    def __init__(self, count: int = 0) -> None:

        if count < 0:
            raise ValueError(
                "count cannot be negative."
            )

        self._count = count

        self._index = 0 if count > 0 else -1

        self._listeners: list[Callable[[int], None]] = []

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def index(self) -> int:
        return self._index

    @property
    def count(self) -> int:
        return self._count

    @property
    def is_empty(self) -> bool:
        return self._count == 0

    @property
    def can_go_next(self) -> bool:
        return self._index < self._count - 1

    @property
    def can_go_previous(self) -> bool:
        return self._index > 0

    @property
    def is_first(self) -> bool:
        return self._index == 0

    @property
    def is_last(self) -> bool:
        return self._index == self._count - 1

    # ---------------------------------------------------------
    # Movement
    # ---------------------------------------------------------

    def next(self) -> int:
        """
        Move to the next item, if any.
        """

        if self.can_go_next:
            self._set_index(self._index + 1)

        return self._index

    def previous(self) -> int:
        """
        Move to the previous item, if any.
        """

        if self.can_go_previous:
            self._set_index(self._index - 1)

        return self._index

    def first(self) -> int:
        """
        Jump to the first item.
        """

        if self._count > 0:
            self._set_index(0)

        return self._index

    def last(self) -> int:
        """
        Jump to the last item.
        """

        if self._count > 0:
            self._set_index(self._count - 1)

        return self._index

    def go_to(self, index: int) -> int:
        """
        Jump to a specific index.
        """

        if not (0 <= index < self._count):
            raise IndexError(
                f"Index {index} out of range "
                f"for count {self._count}."
            )

        self._set_index(index)

        return self._index

    # ---------------------------------------------------------
    # Resizing
    # ---------------------------------------------------------

    def set_count(self, count: int) -> None:
        """
        Update the total number of items, adjusting the current
        index so it remains within bounds.
        """

        if count < 0:
            raise ValueError(
                "count cannot be negative."
            )

        self._count = count

        if count == 0:
            self._set_index(-1)

        elif self._index < 0 or self._index >= count:
            self._set_index(count - 1)

    # ---------------------------------------------------------
    # Listeners
    # ---------------------------------------------------------

    def subscribe(
        self,
        callback: Callable[[int], None],
    ) -> None:

        if callback not in self._listeners:
            self._listeners.append(callback)

    def unsubscribe(
        self,
        callback: Callable[[int], None],
    ) -> None:

        if callback in self._listeners:
            self._listeners.remove(callback)

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _set_index(self, index: int) -> None:

        if index != self._index:

            self._index = index

            for listener in list(self._listeners):
                listener(self._index)

    def __repr__(self) -> str:

        return (
            "NavigationController("
            f"index={self._index}, count={self._count}"
            ")"
        )
