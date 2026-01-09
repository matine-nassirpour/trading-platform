from dataclasses import dataclass

from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_id import EventId
from quantum.domain.shared_kernel.events.event_sequence import EventSequence


@dataclass(frozen=True)
class EventEnvelope:
    """
    Audit-grade event wrapper.

    Guarantees:
    - Global identity
    - Stream ordering
    - Payload immutability
    """

    id: EventId
    sequence: EventSequence
    event: BaseEvent
