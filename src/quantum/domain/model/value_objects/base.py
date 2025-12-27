from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class _HasValue(Protocol):
    value: Any


@dataclass(frozen=True)
class ValueObject(ABC):
    """
    Canonical base class for all Value Objects.

    Guarantees:
    - Immutability
    - Equality by value
    - Mandatory invariant validation
    """

    def __post_init__(self) -> None:
        self._validate()

    @abstractmethod
    def _validate(self) -> None:
        """Must enforce all invariants. Mandatory."""
        raise NotImplementedError

    def __str__(self) -> str:
        assert isinstance(self, _HasValue)
        return str(self.value)

    def __repr__(self) -> str:
        assert isinstance(self, _HasValue)
        cls = self.__class__.__name__
        return f"{cls}(value={self.value!r})"
