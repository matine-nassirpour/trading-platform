from __future__ import annotations

from typing import Any

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.construction_context import (
    is_in_construction,
)
from quantum.domain.shared_kernel.primitives.mutation_key import MutationKey


class ImmutableDomainObject:
    """
    Capability-based immutable domain object with a formal construction window.
    """

    __slots__ = ("_mutation_key",)

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        object.__setattr__(obj, "_mutation_key", MutationKey())
        return obj

    def __setattr__(self, name: str, value: Any) -> None:
        # Allow dataclass-generated __init__ ONLY during construction
        if is_in_construction():
            object.__setattr__(self, name, value)
            return

        raise InvariantViolation(
            f"{self.__class__.__name__} is immutable. "
            "Mutation is only allowed during controlled construction."
        )

    # --- Internal mutation primitive ------------------------------------------

    def _mutate(self, key: MutationKey, name: str, value: Any) -> None:
        if not key._matches(self._mutation_key):
            raise InvariantViolation("Invalid or revoked mutation authority")

        object.__setattr__(self, name, value)

    # --- Capability factory ---------------------------------------------------

    def _mutation_capability(self) -> MutationKey:
        # Not exposed outside the domain; used only by validation pipeline
        return self._mutation_key

    # --- Finalizer ------------------------------------------------------------

    def _revoke_mutation_capability(self) -> None:
        self._mutation_key._invalidate()
