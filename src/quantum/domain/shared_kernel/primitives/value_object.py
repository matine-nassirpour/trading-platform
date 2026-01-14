from abc import ABC, abstractmethod

from quantum.domain.shared_kernel.primitives.structural_contract import (
    enforce_frozen_slot_dataclass_contract,
)


class ValueObject(ABC):
    """
    Canonical base class for all Value Objects.

    HARD GUARANTEES:
    - Must be a frozen dataclass
    - Must use __slots__ (no instance __dict__)
    - No __weakref__
    - Fully validated at construction
    - Value-based equality
    - No partial or invalid state possible
    """

    # --- Compile-time structural contract -------------------------------------

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        # Do not validate the abstract base class itself
        if cls is ValueObject:
            return

        enforce_frozen_slot_dataclass_contract(cls)

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
