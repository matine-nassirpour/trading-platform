from __future__ import annotations

from abc import ABC, abstractmethod

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
            self._revoke_mutation_capability()

    # --- Hooks ----------------------------------------------------------------

    def _validate_base(self, key: MutationKey) -> None:
        pass

    @abstractmethod
    def _validate_semantics(self, key: MutationKey) -> None:
        """
        Domain-specific invariants.

        MUST be implemented by concrete subclasses.
        """
        raise NotImplementedError

    # --- Guard against override -----------------------------------------------

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if not getattr(cls, "__is_immutable_dataclass__", False):
            raise TypeError(
                f"{cls.__name__} must be decorated with @immutable_dataclass"
            )
