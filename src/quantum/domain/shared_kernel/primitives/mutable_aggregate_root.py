from __future__ import annotations

from abc import ABC
from typing import Any

from quantum.domain.shared_kernel.architecture.domain_object import DomainObject
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.aggregate_mutation_guard import (
    AggregateMutationGuard,
)


class MutableAggregateRoot(DomainObject, AggregateMutationGuard, ABC):
    """
    Aggregate mutation gate.

    HARD GUARANTEES:
    - Attributes of the aggregate object itself are NEVER mutated.
    - All state must go through _AggregateState via _mutate().
    - Mutation authority is instance-scoped, async-safe, and non-forgeable.
    """

    def __init__(self) -> None:
        super().__init__()

    # --- Attribute write protection ------------------------------------------

    def __setattr__(self, name: str, value: Any) -> None:
        raise InvariantViolation(
            f"{self.__class__.__name__}: direct attribute mutation is forbidden. "
            "All aggregate state must go through domain events."
        )

    # --- Controlled state write ----------------------------------------------

    def _assert_mutating(self) -> None:
        super()._assert_mutating()
