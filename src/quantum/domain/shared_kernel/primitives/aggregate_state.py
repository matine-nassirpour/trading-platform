from abc import ABC, abstractmethod

from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.primitives.structural_contract import (
    enforce_frozen_slot_dataclass_contract,
)


class AggregateState(ABC):
    """
    Typed, immutable, audit-grade aggregate state capsule.

    HARD GUARANTEES:
    - Validation cannot be bypassed
    - Validation always executed exactly once
    """

    # --- Class creation enforcement -------------------------------------------

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if cls is AggregateState:
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
        Enforces all aggregate invariants.

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

    # --- Mandatory domain contracts -------------------------------------------

    @abstractmethod
    def last_event_sequence(self) -> EventSequence:
        """
        Returns the last applied EventSequence for this state.
        """
        raise NotImplementedError
