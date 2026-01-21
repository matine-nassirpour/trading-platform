from abc import ABC, abstractmethod
from dataclasses import dataclass

from quantum.domain.shared_kernel.primitives.structural_contract import (
    enforce_frozen_slot_dataclass_contract,
)


@dataclass(frozen=True, slots=True)
class Cursor(ABC):
    """
    Monotonic, audit-grade cursor.

    A Cursor represents a strictly ordered position in a domain stream
    (e.g. event sequence, market feed, etc).
    """

    # --- Class creation enforcement -------------------------------------------

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if cls is Cursor:
            return

        if "__post_init__" in cls.__dict__:
            raise TypeError(
                f"{cls.__name__} must NOT override __post_init__. "
                f"Use _validate() instead."
            )

        enforce_frozen_slot_dataclass_contract(cls)

    # --- Domain Contract ------------------------------------------------------

    @abstractmethod
    def _validate(self) -> None:
        """
        Enforces all cursor invariants.

        Must raise DomainError / InvariantViolation on failure.
        """
        raise NotImplementedError

    # --- Construction Guarantee -----------------------------------------------

    def _run_validation(self) -> None:
        """
        Non-overridable validation entrypoint.
        """
        self._validate()

    def __post_init__(self) -> None:
        """
        FINAL — must never be overridden.
        """
        self._run_validation()
