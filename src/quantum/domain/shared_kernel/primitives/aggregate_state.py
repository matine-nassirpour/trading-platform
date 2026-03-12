from abc import ABC, abstractmethod
from dataclasses import dataclass

from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.primitives._validated_frozen_dataclass import (
    _ValidatedFrozenDataclass,
)


@dataclass(frozen=True, slots=True)
class AggregateState(_ValidatedFrozenDataclass, ABC):
    """
    Typed, immutable, audit-grade aggregate state capsule.

    Architectural doctrine:
        - Aggregate identity is ROOT-OWNED.
        - Aggregate state is intentionally IDENTITY-FREE.
        - State carries only business state required for deterministic replay.
        - The root is the sole canonical owner of aggregate identity.
    """

    @abstractmethod
    def last_event_sequence(self) -> EventSequence:
        """
        Returns the last applied EventSequence for this state.
        """
        raise NotImplementedError
