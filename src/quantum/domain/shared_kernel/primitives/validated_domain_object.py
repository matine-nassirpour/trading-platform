from abc import ABC, abstractmethod

from quantum.domain.shared_kernel.primitives.structural_contract import (
    _validate_structural_contract,
)


class ValidatedDomainObject(ABC):
    """
    Canonical structural base for all critical domain objects.

    GUARANTEES:
    - must be a dataclass
    - must be frozen
    - must use slots-only layout
    - must not expose __dict__
    - must not expose __weakref__
    - validation pipeline is centralized
    - __post_init__ must not be overridden by subclasses

    IMPORTANT:
    This base enforces STRUCTURAL discipline.
    It does NOT automatically enforce recursive deep immutability of fields.
    Specialized subclasses may add stronger guarantees.
    """

    __slots__ = ()

    # --- Class creation enforcement -------------------------------------------

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if cls is ValidatedDomainObject:
            return

        if "__post_init__" in cls.__dict__:
            raise TypeError(
                f"{cls.__name__} must NOT override __post_init__. "
                "Use _validate() and optional protected hooks instead."
            )

    # --- Mandatory domain contract --------------------------------------------

    @abstractmethod
    def _validate(self) -> None:
        """
        Enforces semantic invariants of the concrete domain object.

        Must raise DomainError / InvariantViolation on failure.
        """
        raise NotImplementedError

    def _validate_structure(self) -> None:
        """
        Structural validation hook.

        Base implementation enforces the canonical structural contract.
        Specialized structural bases may strengthen it.
        """
        _validate_structural_contract(type(self))

    # --- Construction Guarantee -----------------------------------------------

    def __post_init__(self) -> None:
        """
        Central construction pipeline. Must never be overridden.
        """
        self._validate_structure()
        self._validate()
