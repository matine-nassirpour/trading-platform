from abc import ABC, abstractmethod
from typing import ClassVar, final

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

    _STRUCTURAL_POLICY: ClassVar[StructuralPolicy] = CompositeStructuralPolicy(
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
                "_STRUCTURAL_POLICY instead."
            )

    # --- Mandatory domain contract --------------------------------------------

    @classmethod
    @final
    def _structural_policy(cls) -> StructuralPolicy:
        """
        Returns the structural policy applied to this concrete type.

        This method is intentionally final:
        - policy variation must happen through the _STRUCTURAL_POLICY class
          attribute;
        - this preserves a single, inspectable, deterministic resolution path;
        - it prevents ad-hoc method overrides from fragmenting the construction
          contract across the hierarchy.
        """
        return cls._STRUCTURAL_POLICY

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
        type(self)._structural_policy().validate_instance(self)
        self._validate_semantics()
