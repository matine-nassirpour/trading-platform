from abc import ABC, abstractmethod


class ValidatableAggregate(ABC):
    """
    Contract enforced on all event-sourced aggregates.

    Guarantees:
    - Every aggregate state is explicitly validated
    - Replay cannot produce silent corruption
    - Auditors can see and verify all invariants
    """

    @abstractmethod
    def _validate_state(self) -> None:
        """
        Validates ALL aggregate invariants.

        Must raise InvariantViolation on any breach.
        """
        raise NotImplementedError
