from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, fields, is_dataclass
from typing import Any, ClassVar

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.domain_object import DomainObject
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation


@dataclass(frozen=False)
class ValueObject(DomainObject, ABC):
    """
    Abstract base class for all Value Objects.

    HARD GUARANTEE:
    - __post_init__ is FINAL
    - Validation pipeline is deterministic and non-bypassable
    """

    # Internal guard: instance-level, not class-level
    _is_initializing: ClassVar[str] = "_vo_is_initializing"

    # --- Architecture ---------------------------------------------------------

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    # --- FINAL initialization pipeline ----------------------------------------

    def __post_init__(self) -> None:
        """
        FINAL. Must never be overridden.
        """
        object.__setattr__(self, self._is_initializing, True)
        try:
            self._run_validation()
        finally:
            object.__setattr__(self, self._is_initializing, False)

    def _run_validation(self) -> None:
        """
        FINAL. Orchestrates validation in a fixed, auditable order.
        """
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

    # --- Mutation barrier -----------------------------------------------------

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Prevents any mutation outside of the construction window.
        """
        if not getattr(self, self._is_initializing, False):
            raise InvariantViolation(
                f"{self.__class__.__name__} is immutable. "
                f"Illegal attempt to modify attribute '{name}'."
            )
        object.__setattr__(self, name, value)

    # --- Guard against override -----------------------------------------------

    def __init_subclass__(cls) -> None:
        # Enforce dataclass(frozen=True)
        if not is_dataclass(cls):
            raise TypeError(f"{cls.__name__} must be a @dataclass(frozen=True)")

        params = getattr(cls, "__dataclass_params__", None)
        if not params or not params.frozen:
            raise TypeError(f"{cls.__name__} must be declared with frozen=True")

        # Forbid overriding FINAL methods
        forbidden = {"__post_init__", "_run_validation"}
        for name in forbidden:
            if name in cls.__dict__:
                raise TypeError(
                    f"{cls.__name__} is not allowed to override {name} "
                    "(ValueObject validation pipeline is final)"
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
