from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope


@runtime_checkable
class EventPublisher(Protocol):
    """
    Publishes domain events to the outside world (message bus, log, outbox, etc.).

    Requirements for implementations (infra concern):
    - at-least-once or exactly-once semantics as required
    - ordering guarantees if needed (aggregate event order)
    - durability if required (outbox pattern recommended)
    """

    def publish(self, envelope: EventEnvelope) -> None:
        raise NotImplementedError
