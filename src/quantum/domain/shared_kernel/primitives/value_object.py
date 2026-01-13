from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import is_dataclass

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.domain_object import DomainObject
from quantum.domain.shared_kernel.primitives.immutable_domain_object import (
    ImmutableDomainObject,
)
from quantum.domain.shared_kernel.primitives.mutation_key import MutationKey


class ValueObject(DomainObject, ImmutableDomainObject, ABC):
    """
    Canonical base class for all Value Objects.

    HARD GUARANTEES:
    - Strict immutability enforced by capability-based mutation authority
    - All invariants are executed exactly once during construction
    - No invariant can be bypassed
    - No mutation is possible after construction
    """

    # --- Architecture ---------------------------------------------------------

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    # --- FINAL initialization pipeline ----------------------------------------

    def __post_init__(self) -> None:
        key: MutationKey = self._mutation_capability()

        try:
            self._validate_base(key)
            self._validate_semantics(key)
        finally:
            # Mutation authority is permanently revoked, never removed
            self._revoke_mutation_capability()

    # --- Hooks ----------------------------------------------------------------

    def _validate_base(self, key: MutationKey) -> None:
        """
        Base invariants for all ValueObjects.
        Default: none.

        This method MAY mutate the instance using:
            self._mutate(key, name, value)
        """
        pass

    @abstractmethod
    def _validate_semantics(self, key: MutationKey) -> None:
        """
        Domain-specific invariants.

        MUST be implemented by concrete subclasses.

        This method MAY normalize or canonicalize fields using:
            self._mutate(key, name, value)
        """
        raise NotImplementedError

    # --- Guard against override -----------------------------------------------

    def __init_subclass__(cls) -> None:
        """
        Enforces architectural correctness of all ValueObject subclasses.
        """
        super().__init_subclass__()

        if not is_dataclass(cls):
            raise TypeError(f"{cls.__name__} must be a dataclass")
