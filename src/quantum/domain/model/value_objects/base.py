from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class _HasValue(Protocol):
    value: Any


@dataclass(frozen=True)
class ValueObject:
    """
    Canonical base class for all Value Objects.

    Guarantees:
    - Immutability
    - Equality by value
    - Hash ability
    """

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        """Override in subclasses to enforce invariants."""
        pass

    def __str__(self) -> str:
        assert isinstance(self, _HasValue)
        return str(self.value)

    def __repr__(self) -> str:
        assert isinstance(self, _HasValue)
        cls = self.__class__.__name__
        return f"{cls}(value={self.value!r})"
