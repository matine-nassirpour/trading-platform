from __future__ import annotations

from typing import Any

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.mutation_key import MutationKey


class ImmutableDomainObject:
    """
    Capability-based immutable domain object.

    Guarantees:
    - Each instance owns a unique mutation capability
    - No mutation is possible outside the construction window
    - No dataclass or Python feature can bypass this contract
    """

    __slots__ = ("_mutation_key",)

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        object.__setattr__(obj, "_mutation_key", MutationKey())
        return obj

    def __setattr__(self, name: str, value: Any) -> None:
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
        """
        Returns the ONLY key capable of mutating this instance.
        Not copyable, not serializable, not global.
        """
        return self._mutation_key

    # --- Finalizer ------------------------------------------------------------

    def _revoke_mutation_capability(self) -> None:
        self._mutation_key._invalidate()
