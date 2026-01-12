from __future__ import annotations

from typing import Any


class _AggregateState:
    """
    Internal, write-protected aggregate state capsule.

    This object is NEVER exposed to user code.
    All mutations must go through the AggregateRoot engine.
    """

    __slots__ = ("_data",)

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def get(self, name: str) -> Any:
        return self._data.get(name)

    def _set(self, name: str, value: Any) -> None:
        self._data[name] = value
