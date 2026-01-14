from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import is_dataclass

from quantum.domain.shared_kernel.events.event_sequence import EventSequence


def _assert_is_dataclass(cls: type) -> None:
    if not is_dataclass(cls):
        raise TypeError(f"{cls.__name__} must be a dataclass")


def _assert_frozen(cls: type) -> None:
    if not cls.__dataclass_params__.frozen:
        raise TypeError(f"{cls.__name__} must be frozen=True")


def _assert_slots_enabled(cls: type) -> None:
    if not cls.__dataclass_params__.slots:
        raise TypeError(f"{cls.__name__} must be slots=True")


def _get_slots(cls: type) -> Iterable[str]:
    slots = cls.__dict__.get("__slots__")

    if slots is None:
        raise TypeError(f"{cls.__name__} must define __slots__")

    if isinstance(slots, str):
        return (slots,)

    return tuple(slots)


def _assert_no_dict_or_weakref(cls: type) -> None:
    slots = _get_slots(cls)

    if "__dict__" in slots:
        raise TypeError(f"{cls.__name__} must not include '__dict__' in __slots__")

    if "__weakref__" in slots:
        raise TypeError(f"{cls.__name__} must not include '__weakref__' in __slots__")


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

        _assert_is_dataclass(cls)
        _assert_frozen(cls)
        _assert_slots_enabled(cls)
        _assert_no_dict_or_weakref(cls)

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
