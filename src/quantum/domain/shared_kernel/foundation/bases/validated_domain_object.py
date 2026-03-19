from abc import ABC, abstractmethod
from typing import ClassVar

from quantum.domain.shared_kernel.foundation.contracts.policies import StructuralPolicy
from quantum.domain.shared_kernel.foundation.contracts.structural_policy import (
    CompositeStructuralPolicy,
    PythonDataclassRepresentationPolicy,
)


class ValidatedDomainObject(ABC):
    """
    Canonical base for structurally validated domain objects.

    DESIGN PRINCIPLES:
    - structural validation is centralized;
    - structure and semantics are separate concerns;
    - structural policy is explicit and replaceable;
    - this base enforces only the default representation discipline;
    - stronger guarantees are added by specialized subclasses.

    IMPORTANT:
    Subclasses must be dataclasses themselves.
    """

    __slots__ = ()

    __structural_policy__: ClassVar[StructuralPolicy] = CompositeStructuralPolicy(
        policies=(PythonDataclassRepresentationPolicy(),)
    )

    # --- Class creation enforcement -------------------------------------------

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if cls is ValidatedDomainObject:
            return

        if "__post_init__" in cls.__dict__:
            raise TypeError(
                f"{cls.__name__} must not override __post_init__. "
                "Override _validate_semantics() and, if strictly necessary, "
                "_structural_policy() instead."
            )

    # --- Mandatory domain contract --------------------------------------------

    @classmethod
    def _structural_policy(cls) -> StructuralPolicy:
        """
        Returns the structural policy applied to this concrete type.

        Subclasses may override this if they need a different composition,
        though specialized base classes are preferred over ad-hoc overrides.
        """
        return cls.__structural_policy__

    def _validate_structure(self) -> None:
        """
        Executes structural validation according to the configured policy.
        """
        type(self)._structural_policy().validate_instance(self)

    @abstractmethod
    def _validate_semantics(self) -> None:
        """
        Enforces semantic domain invariants.

        Must raise DomainError / InvariantViolation on failure.
        """
        raise NotImplementedError

    # --- Construction Guarantee -----------------------------------------------

    def __post_init__(self) -> None:
        """
        Final construction pipeline:
        1. structural validation
        2. semantic validation
        """
        self._validate_structure()
        self._validate_semantics()
