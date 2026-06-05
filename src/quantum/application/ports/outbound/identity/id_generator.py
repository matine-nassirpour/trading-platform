from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.event_sourcing.events.event_id import EventId


@runtime_checkable
class IdGenerator(Protocol):
    def new_event_id(self) -> EventId: ...
