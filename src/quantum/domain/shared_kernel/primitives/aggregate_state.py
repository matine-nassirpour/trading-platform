import inspect

from abc import ABC, abstractmethod

from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.primitives.structural_contract import (
    enforce_frozen_slot_dataclass_contract,
)


class AggregateState(ABC):
    """
    Typed, immutable, audit-grade aggregate state capsule.

    HARD GUARANTEES:
    - Must be a frozen dataclass
    - Must use __slots__
    - No __dict__, no __weakref__
    - All invariants enforced at construction
    - State is fully statically discoverable
    """

    __slots__ = ()

    # --- Compile-time structural contract -------------------------------------

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        # Do not validate the abstract base class itself
        if cls is AggregateState:
            return

        if inspect.isabstract(cls):
            return

        enforce_frozen_slot_dataclass_contract(cls)

    # --- Runtime invariant enforcement ---------------------------------------

    @abstractmethod
    def _validate(self) -> None:
        """
        Enforces ALL aggregate invariants.

        Must raise InvariantViolation on any breach.
        """
        raise NotImplementedError

    def __post_init__(self) -> None:
        self._validate()

    # --- Mandatory domain contracts -------------------------------------------

    @abstractmethod
    def last_event_sequence(self) -> EventSequence:
        """
        Returns the last applied EventSequence for this state.
        """
        raise NotImplementedError
