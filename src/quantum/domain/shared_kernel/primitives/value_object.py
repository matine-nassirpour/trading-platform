from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, fields, is_dataclass
from typing import ClassVar

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

    # Internal guard: allows controlled mutation only during validation
    _is_fully_initialized: ClassVar[bool] = False

    # --- Architecture ---------------------------------------------------------

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    # --- FINAL initialization pipeline ----------------------------------------

    def __post_init__(self) -> None:
        # Allow controlled mutation during validation
        object.__setattr__(self, "_ValueObject__is_fully_initialized", False)

        self.__validate()

        # Lock the object forever
        object.__setattr__(self, "_ValueObject__is_fully_initialized", True)

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
        # Enforce dataclass(frozen=True)
        if not is_dataclass(cls):
            raise TypeError(f"{cls.__name__} must be a frozen dataclass")

        params = getattr(cls, "__dataclass_params__", None)
        if not params or not params.frozen:
            raise TypeError(
                f"{cls.__name__} must be declared with @dataclass(frozen=True)"
            )

        # Forbid any override of the construction & validation pipeline
        forbidden = {"__init__", "__post_init__", "__validate"}
        for name in forbidden:
            if name in cls.__dict__:
                raise TypeError(
                    f"{cls.__name__} is not allowed to override {name} "
                    "(ValueObject construction pipeline is final)"
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
