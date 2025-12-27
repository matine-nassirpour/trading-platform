from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ValueObject(ABC):
    """
    Canonical base class for all Value Objects.

    Guarantees:
    - Immutability
    - Equality by structural value
    - Explicit invariant validation
    - Zero assumptions about internal shape
    """

    def __post_init__(self) -> None:
        self._validate()

    @abstractmethod
    def _validate(self) -> None:
        """
        Enforces all invariants of the Value Object.
        Must be implemented by subclasses.
        """
        raise NotImplementedError

    # --- Canonical string representations -------------------------------------

    def __repr__(self) -> str:
        cls_name = self.__class__.__name__
        args = ", ".join(
            f"{field.name}={getattr(self, field.name)!r}" for field in fields(self)
        )
        return f"{cls_name}({args})"

    def __str__(self) -> str:
        """
        Human-readable but deterministic representation.
        Safe for logging/debugging.
        """
        return self.__repr__()
