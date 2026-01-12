from __future__ import annotations

from abc import ABC
from typing import Any

from quantum.domain.shared_kernel.architecture.domain_object import DomainObject
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation


class MutableAggregateRoot(DomainObject, ABC):
    """
    Base class for aggregates that are mutable via domain events only.
    """

    _MUTATING = False

    def __setattr__(self, name: str, value: Any) -> None:
        if not self._MUTATING:
            raise InvariantViolation(
                f"Direct mutation of aggregate {self.__class__.__name__} is forbidden"
            )
        object.__setattr__(self, name, value)

    # --- mutation control -----------------------------------------------------

    def _begin_mutation(self) -> None:
        object.__setattr__(self, "_MUTATING", True)

    def _end_mutation(self) -> None:
        object.__setattr__(self, "_MUTATING", False)

    def _assert_mutating(self) -> None:
        if not self._MUTATING:
            raise InvariantViolation(
                f"{self.__class__.__name__} state mutation outside event application"
            )
