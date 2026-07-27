"""
ScrollSnap
==========

Serialization Utilities

Shared serialization helpers for ScrollSnap models.

These helpers provide consistent serialization of dataclasses,
Enums, datetime objects and pathlib.Path instances.

This module intentionally contains no project-specific logic.
"""

from __future__ import annotations

from dataclasses import asdict, fields, is_dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Type, TypeVar

T = TypeVar("T")


# ---------------------------------------------------------
# Primitive Serialization
# ---------------------------------------------------------


def serialize(value: Any) -> Any:
    """
    Recursively serialize an object into JSON-compatible values.
    """

    if value is None:
        return None

    if isinstance(value, Enum):
        return value.name

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, Path):
        return str(value)

    if is_dataclass(value):
        return {
            field.name: serialize(
                getattr(value, field.name)
            )
            for field in fields(value)
        }

    if isinstance(value, list):
        return [
            serialize(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            serialize(item)
            for item in value
        ]

    if isinstance(value, dict):
        return {
            key: serialize(val)
            for key, val in value.items()
        }

    return value


# ---------------------------------------------------------
# Dataclass Serialization
# ---------------------------------------------------------


def dataclass_to_dict(obj: Any) -> dict[str, Any]:
    """
    Serialize a dataclass.

    Raises
    ------
    TypeError
        If obj is not a dataclass.
    """

    if not is_dataclass(obj):
        raise TypeError(
            f"{type(obj).__name__} is not a dataclass."
        )

    return serialize(obj)


# ---------------------------------------------------------
# Utility
# ---------------------------------------------------------


def copy_dataclass(instance: T) -> T:
    """
    Deep-copy a dataclass using serialization.

    This works well for immutable value objects.
    """

    cls: Type[T] = type(instance)

    if not is_dataclass(instance):
        raise TypeError(
            f"{cls.__name__} is not a dataclass."
        )

    return cls(**asdict(instance))