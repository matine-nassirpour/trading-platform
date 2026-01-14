from abc import ABC, abstractmethod

from quantum.domain.shared_kernel.events.event_sequence import EventSequence


class AggregateState(ABC):
    """
    Typed, declarative aggregate state capsule.

    HARD GUARANTEES:
    - State is explicit (fields are declared via __slots__)
    - No dynamic attribute injection (__dict__ forbidden)
    - Audit-grade: all state fields are discoverable by static inspection
    """

    __slots__ = ()

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

    # --- Compile-time structural contract -------------------------------------

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        # Do not validate the abstract base class itself
        if cls is AggregateState:
            return

        # Must explicitly declare __slots__
        if "__slots__" not in cls.__dict__:
            raise TypeError(f"{cls.__name__} must explicitly declare __slots__")

        slots = cls.__dict__["__slots__"]

        # Slots must not be empty
        if slots is None or slots == () or slots == "":
            raise TypeError(f"{cls.__name__} must not have empty __slots__")

        # Normalize to tuple
        if isinstance(slots, str):
            slots_tuple = (slots,)
        else:
            slots_tuple = tuple(slots)

        # __dict__ is forbidden
        if "__dict__" in slots_tuple:
            raise TypeError(f"{cls.__name__} must not include '__dict__' in __slots__")

        # __weakref__ is forbidden (breaks auditability)
        if "__weakref__" in slots_tuple:
            raise TypeError(
                f"{cls.__name__} must not include '__weakref__' in __slots__"
            )
