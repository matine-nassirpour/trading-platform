from __future__ import annotations

from abc import ABC
from typing import Any

from quantum.domain.shared_kernel.architecture.domain_object import DomainObject
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation


class MutableAggregateRoot(DomainObject, ABC):
    """
    Aggregate mutation gate.

    HARD GUARANTEES:
    - Attributes of the aggregate object itself are NEVER mutated.
    - All state must go through _AggregateState via _mutate().
    - Even event handlers cannot bypass this.
    """

    _MUTATING = False

    def __setattr__(self, name: str, value: Any) -> None:
        # During mutation, ONLY _state is allowed to be assigned
        if self._MUTATING:
            if name != "_state":
                raise InvariantViolation(
                    f"{self.__class__.__name__}: illegal mutation of attribute '{name}'. "
                    "All aggregate state must be modified via _mutate()."
                )
            object.__setattr__(self, name, value)
            return

        # Outside mutation, nothing may be written
        raise InvariantViolation(
            f"{self.__class__.__name__}: direct attribute mutation is forbidden"
        )

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
