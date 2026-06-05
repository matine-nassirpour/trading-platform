from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.event_sourcing.events.recorded_event_envelope import (
    RecordedEventEnvelope,
)


@runtime_checkable
class DomainEventDispatcher(Protocol):
    """
    Inbound application port for dispatching domain events to application handlers.

    Responsibility:
    - Register application-level handlers.
    - Dispatch recorded domain events to interested handlers.
    - Coordinate in-process event reaction.

    Non-responsibilities:
    - No transport concern.
    - No broker publishing.
    - No outbox persistence.
    - No external integration event publishing.
    """

    async def dispatch(
        self,
        events: Sequence[RecordedEventEnvelope],
    ) -> None:
        """
        Dispatch persisted events to registered in-process handlers.
        """
        ...
