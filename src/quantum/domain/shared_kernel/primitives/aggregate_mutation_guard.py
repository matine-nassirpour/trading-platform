from __future__ import annotations

import contextvars
import secrets

from collections.abc import Iterator
from contextlib import contextmanager

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation

# Context variable storing the active aggregate mutation token
_ACTIVE_AGGREGATE_MUTATION_TOKEN: contextvars.ContextVar[str | None] = (
    contextvars.ContextVar(
        "_ACTIVE_AGGREGATE_MUTATION_TOKEN",
        default=None,
    )
)


class AggregateMutationGuard:
    """
    Per-instance, non-forgeable, async-safe mutation authority
    for Event-Sourced Aggregates.
    """

    __slots__ = ("_mutation_token",)

    def __init__(self) -> None:
        super().__init__()
        # Each aggregate instance gets its own unforgeable token
        self._mutation_token: str = secrets.token_hex(32)

    def _assert_mutating(self) -> None:
        active = _ACTIVE_AGGREGATE_MUTATION_TOKEN.get()
        if active != self._mutation_token:
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
        - non-forgeable
        """
        reset = _ACTIVE_AGGREGATE_MUTATION_TOKEN.set(self._mutation_token)
        try:
            yield
        finally:
            _ACTIVE_AGGREGATE_MUTATION_TOKEN.reset(reset)
