from abc import ABC, abstractmethod
from dataclasses import is_dataclass


class ValueObject(ABC):
    """
    Canonical base class for all Value Objects.

    Guarantees:
    - Immutable (all subclasses should be frozen + slots)
    - Comparable by value
    - Fully validated at construction
    - No partial or invalid state possible
    """

    # --- Compile-time structural contract -------------------------------------

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        # Do not validate the abstract base class itself
        if cls is ValueObject:
            return

        # Must be a dataclass
        if not is_dataclass(cls):
            raise TypeError(f"{cls.__name__} must be a dataclass")

        params = cls.__dataclass_params__  # type: ignore[attr-defined]

        # Must be frozen (immutable)
        if not params.frozen:
            raise TypeError(f"{cls.__name__} must be frozen=True")

        # Must use slots
        if not params.slots:
            raise TypeError(f"{cls.__name__} must be slots=True")

        # __dict__ must not exist
        if hasattr(cls, "__dict__"):
            raise TypeError(f"{cls.__name__} must not have __dict__")

        # __weakref__ must not exist
        if hasattr(cls, "__weakref__"):
            raise TypeError(f"{cls.__name__} must not have __weakref__")

    # --- Invariant ------------------------------------------------------------

    @abstractmethod
    def _validate(self) -> None:
        """
        Enforce all domain invariants.
        Must raise a domain error on any violation.
        """
        raise NotImplementedError

    def __post_init__(self) -> None:
        self._validate()
