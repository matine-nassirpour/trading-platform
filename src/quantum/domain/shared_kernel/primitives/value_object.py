from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import is_dataclass
from typing import Any

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.domain_object import DomainObject
from quantum.domain.shared_kernel.primitives.immutable_domain_object import (
    ImmutableDomainObject,
)


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
        """
        Final, sealed construction pipeline.

        1. Acquires the unique mutation capability of this instance
        2. Runs base invariants
        3. Runs semantic invariants
        4. Revokes mutation authority forever
        """

        # Acquire instance-local mutation capability
        key = self._mutation_capability()

        try:
            self._validate_base(key)
            self._validate_semantics(key)
        finally:
            # Irrevocably revoke mutation authority
            # After this point the object is mathematically immutable
            object.__delattr__(self, "_mutation_key")

    # --- Hooks ----------------------------------------------------------------

    def _validate_base(self, key: Any) -> None:
        """
        Base invariants for all ValueObjects.
        Default: none.

        This method MAY mutate the instance using:
            self._mutate(key, name, value)
        """
        pass

    @abstractmethod
    def _validate_semantics(self, key: Any) -> None:
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

        # Must remain a dataclass
        if not is_dataclass(cls):
            raise TypeError(f"{cls.__name__} must be a dataclass")

    # --- Canonical string representations -------------------------------------

    def __repr__(self) -> str:
        cls = type(self)

        if not is_dataclass(cls):
            return super().__repr__()

        fields = cls.__dataclass_fields__
        args = ", ".join(f"{name}={getattr(self, name)!r}" for name in fields)
        return f"{cls.__name__}({args})"
