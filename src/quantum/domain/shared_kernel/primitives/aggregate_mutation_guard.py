from __future__ import annotations

import contextvars

from collections.abc import Iterator
from contextlib import contextmanager

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation

# Context variable storing the active aggregate mutation identity
_ACTIVE_AGGREGATE_MUTATION_TOKEN: contextvars.ContextVar[object | None] = (
    contextvars.ContextVar("_ACTIVE_AGGREGATE_MUTATION_TOKEN", default=None)
)


class AggregateMutationGuard:
    """
    Per-instance, deterministic, non-forgeable mutation authority
    for Event-Sourced Aggregates.
    """

    __slots__ = ("_mutation_identity",)

    def __init__(self) -> None:
        super().__init__()
        # Deterministic unique identity
        self._mutation_identity = object()

    def _assert_mutating(self) -> None:
        active = _ACTIVE_AGGREGATE_MUTATION_TOKEN.get()
        if active is not self._mutation_identity:
            raise InvariantViolation(
                "Aggregate state mutation outside authorized mutation window"
            )

    @contextmanager
    def _mutation_window(self) -> Iterator[None]:
        """
        Opens a strictly scoped mutation window for THIS aggregate only.

        Guarantees:
        - instance-local
        - thread-safe
        - async-safe
        - deterministic
        """
        token = _ACTIVE_AGGREGATE_MUTATION_TOKEN.set(self._mutation_identity)
        try:
            yield
        finally:
            _ACTIVE_AGGREGATE_MUTATION_TOKEN.reset(token)
