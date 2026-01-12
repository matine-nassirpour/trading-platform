from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, fields

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.domain_object import DomainObject


@dataclass(frozen=True)
class ValueObject(DomainObject, ABC):
    """
    Abstract base class for all Value Objects.

    HARD GUARANTEE:
    - __post_init__ is FINAL
    - Validation pipeline is deterministic and non-bypassable
    """

    # --- Architecture ---------------------------------------------------------

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    # --- FINAL initialization pipeline ----------------------------------------

    def __post_init__(self) -> None:
        self.__validate()

    def __validate(self) -> None:
        """
        FINAL validation entrypoint.

        Order is guaranteed and non-overridable:
        1. base invariants
        2. subclass semantic invariants
        """
        self._validate_base()
        self._validate_semantics()

    # --- Hooks ----------------------------------------------------------------

    def _validate_base(self) -> None:
        """
        Base-level invariants for all ValueObjects.
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
        forbidden = {"__post_init__", "__validate"}

        for name in forbidden:
            if name in cls.__dict__:
                raise TypeError(
                    f"{cls.__name__} is not allowed to override {name} "
                    "(ValueObject initialization pipeline is final)"
                )

        super().__init_subclass__()

    # --- Canonical string representations -------------------------------------

    def __repr__(self) -> str:
        cls_name = self.__class__.__name__
        args = ", ".join(
            f"{field.name}={getattr(self, field.name)!r}" for field in fields(self)
        )
        return f"{cls_name}({args})"

    def __str__(self) -> str:
        return self.__repr__()
