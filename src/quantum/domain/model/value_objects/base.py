from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict


class _HasValue(Protocol):
    value: Any


class ValueObject(BaseModel, _HasValue):
    """
    Canonical base class for all Value Objects.

    Guarantees:
    - Immutability (frozen)
    - Equality by value
    - Hash ability
    - No extra fields
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=False,
        arbitrary_types_allowed=False,
        populate_by_name=True,
    )

    def __eq__(self, other: Any) -> bool:
        return (
            self.__class__ is other.__class__
            and self.model_dump() == other.model_dump()
        )

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.model_dump().items())))

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        cls = self.__class__.__name__
        payload = ", ".join(f"{k}={v!r}" for k, v in self.model_dump().items())
        return f"{cls}({payload})"
