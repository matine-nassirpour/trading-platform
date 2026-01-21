from abc import ABC, abstractmethod

from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.primitives._validated_frozen_dataclass import (
    _ValidatedFrozenDataclass,
)


class AggregateState(_ValidatedFrozenDataclass, ABC):
    """
    Typed, immutable, audit-grade aggregate state capsule.
    """

    @abstractmethod
    def last_event_sequence(self) -> EventSequence:
        """
        Returns the last applied EventSequence for this state.
        """
        raise NotImplementedError
