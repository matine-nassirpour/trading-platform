from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import is_dataclass

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.domain_object import DomainObject
from quantum.domain.shared_kernel.architecture.immutable_dataclass import (
    immutable_dataclass,
)
from quantum.domain.shared_kernel.primitives.immutable_domain_object import (
    ImmutableDomainObject,
)


@immutable_dataclass
class ValueObject(DomainObject, ImmutableDomainObject, ABC):
    """
    Abstract base class for all Value Objects.

    HARD GUARANTEES:
    - Instances are strictly immutable
    - Validation is executed in a controlled initialization window
    - Invariants cannot be bypassed
    """

    # --- Architecture ---------------------------------------------------------

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    # --- FINAL initialization pipeline ----------------------------------------

    def __post_init__(self) -> None:
        # Open a mutation window only for validation / normalization
        with self._mutation_window():
            self._run_validation()

    def _run_validation(self) -> None:
        self._validate_base()
        self._validate_semantics()

    # --- Hooks ----------------------------------------------------------------

    def _validate_base(self) -> None:
        """
        Base invariants for all ValueObjects.
        Default: none.
        """
        pass

    @abstractmethod
    def _validate_semantics(self) -> None:
        """
        Domain-specific invariants.
        MUST be implemented by concrete subclasses.
        """
        raise NotImplementedError

    # --- Guard against override -----------------------------------------------

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

    # --- Canonical string representations -------------------------------------

    def __repr__(self) -> str:
        cls = type(self)

        if not is_dataclass(cls):
            return super().__repr__()

        args = ", ".join(
            f"{name}={getattr(self, name)!r}" for name in cls.__dataclass_fields__
        )
        return f"{cls.__name__}({args})"
