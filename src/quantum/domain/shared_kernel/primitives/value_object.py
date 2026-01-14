from abc import ABC, abstractmethod


class ValueObject(ABC):
    """
    Canonical base class for all Value Objects.

    Guarantees:
    - Immutable
    - Comparable by value
    - Fully validated at construction
    - No partial or invalid state possible
    """

    @abstractmethod
    def _validate(self) -> None:
        """
        Enforce all domain invariants.
        Must raise a domain error on any violation.
        """
        raise NotImplementedError

    def __post_init__(self) -> None:
        self._validate()
