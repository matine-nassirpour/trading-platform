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

    @classmethod
    def _assert_valid_state_type(cls) -> None:
        # Must be slots-based and non-empty, otherwise it becomes non-auditable.
        if "__slots__" not in cls.__dict__:
            raise TypeError(f"{cls.__name__} must declare __slots__")

        slots = cls.__dict__["__slots__"]
        if slots is None or slots == () or slots == "":
            raise TypeError(f"{cls.__name__} must not have empty __slots__")

        # Disallow instance __dict__
        if isinstance(slots, str):
            slots_tuple = (slots,)
        else:
            slots_tuple = tuple(slots)

        if "__dict__" in slots_tuple:
            raise TypeError(f"{cls.__name__} must not include '__dict__' in __slots__")
