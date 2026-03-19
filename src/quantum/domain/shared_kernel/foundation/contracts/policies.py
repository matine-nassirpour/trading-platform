from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@runtime_checkable
class StructuralPolicy(Protocol):
    """
    A structural policy validates one orthogonal architectural concern.

    Examples:
    - Python representation discipline
    - deep immutability
    - forbidden runtime types in domain objects
    """

    def validate_class(self, cls: type) -> None:
        """
        Validates class-level structural constraints.
        Must be deterministic and side-effect free.
        """

    def validate_instance(self, instance: object) -> None:
        """
        Validates instance-level structural constraints.
        Must be deterministic and side-effect free.
        """


@dataclass(frozen=True, slots=True)
class NoOpStructuralPolicy:
    """
    Null structural policy.
    Useful as a default composition element.
    """

    def validate_class(self, cls: type) -> None:
        return None

    def validate_instance(self, instance: object) -> None:
        return None
