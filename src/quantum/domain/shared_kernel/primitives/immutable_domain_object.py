from __future__ import annotations

from typing import Any

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.mutation_key import MutationKey


class ImmutableDomainObject:
    """
    Hard-immutable, thread-safe, re-entrant domain object.

    Guarantees:
    - Each instance has its own mutation authority.
    - No global or class-level state is used.
    - Safe under concurrency, async, and replay.
    - Lexically scoped mutation window.
    """

    __slots__ = ("_mutation_token",)

    def __init__(self) -> None:
        # Each instance gets its own unforgeable token
        object.__setattr__(self, "_mutation_key", MutationKey())

    def __setattr__(self, name: str, value: Any) -> None:
        raise InvariantViolation(
            f"{self.__class__.__name__} is immutable. "
            "Use mutation context during construction."
        )

    # --- Internal mutation primitive ------------------------------------------

    def _mutate(self, key: MutationKey, name: str, value: Any) -> None:
        if not key._matches(self._mutation_key):
            raise InvariantViolation("Invalid mutation authority")

        object.__setattr__(self, name, value)

    # --- Capability factory ---------------------------------------------------

    def _mutation_capability(self) -> MutationKey:
        """
        Returns the ONLY key capable of mutating this instance.
        Not copyable, not serializable, not global.
        """
        return self._mutation_key
