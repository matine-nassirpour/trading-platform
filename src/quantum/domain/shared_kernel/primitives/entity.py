from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Entity(ABC):
    """
    Canonical base class for all domain entities.

    Guarantees:
    - Immutability
    - Explicit invariant validation at construction time
    - Identity-based equality (implemented by subclasses)
    """

    def __post_init__(self) -> None:
        self._validate()

    # --- Invariants -----------------------------------------------------------

    @abstractmethod
    def _validate(self) -> None:
        """
        Enforces all entity invariants.

        Must be:
        - deterministic
        - side-effect free
        - exhaustive
        """
        raise NotImplementedError
