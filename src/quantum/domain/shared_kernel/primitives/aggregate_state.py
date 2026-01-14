from abc import ABC, abstractmethod


class AggregateState(ABC):
    """
    Typed, declarative aggregate state capsule.

    HARD GUARANTEES:
    - State is explicit (fields are declared via __slots__)
    - No dynamic attribute injection (__dict__ forbidden)
    - Audit-grade: all state fields are discoverable by static inspection
    """

    __slots__ = ()

    @abstractmethod
    def _state_contract(self) -> None:
        """
        Architectural anchor.

        Must exist on all concrete AggregateState types.
        It has no runtime semantics; it makes the state type
        formally abstract and contract-bound.
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
