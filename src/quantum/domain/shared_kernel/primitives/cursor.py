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

    # --- Compile-time structural contract -------------------------------------

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        # Do not validate the abstract base class itself
        if cls is Cursor:
            return

        enforce_frozen_slot_dataclass_contract(cls)

    def __post_init__(self) -> None:
        self._validate()

    # --- Invariant ------------------------------------------------------------

    @abstractmethod
    def _validate(self) -> None:
        """
        Enforces all cursor invariants.

        Must be deterministic and side-effect free.
        """
        raise NotImplementedError
