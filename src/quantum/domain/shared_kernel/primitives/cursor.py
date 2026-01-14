from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Cursor(ABC):
    """
    Monotonic, audit-grade cursor.

    A Cursor represents a strictly ordered position in a domain stream
    (e.g. event sequence, market feed, etc).
    """

    def __post_init__(self) -> None:
        self._validate()

    @abstractmethod
    def _validate(self) -> None:
        """
        Enforces all cursor invariants.

        Must be deterministic and side-effect free.
        """
        raise NotImplementedError
