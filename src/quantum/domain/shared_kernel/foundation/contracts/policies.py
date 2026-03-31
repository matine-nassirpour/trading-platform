from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@runtime_checkable
class StructuralPolicy(Protocol):
    """
    A structural policy validates one orthogonal architectural concern.

    IMPORTANT:
    Implementations are expected to be immutable and hashable because composite
    policy validation may be cached by policy tuple + target class.
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
