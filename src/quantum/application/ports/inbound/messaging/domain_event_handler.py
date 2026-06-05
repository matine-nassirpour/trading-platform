from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.event_sourcing.events.recorded_event_envelope import (
    RecordedEventEnvelope,
)


@runtime_checkable
class DomainEventHandler(Protocol):
    """
    Application-level in-process domain event handler.

    Contract:
    - Handles one already-recorded domain event.
    - Must be deterministic.
    - Must not publish to external transports directly.
    - Must be failure-isolated by the dispatcher.
    - May perform asynchronous application work.
    """

    async def handle(self, event: RecordedEventEnvelope) -> None: ...
