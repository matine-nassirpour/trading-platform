from __future__ import annotations

from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.events.base_event import BaseEvent


@runtime_checkable
class DomainEventPublisher(Protocol):
    """
    Publishes domain events to the outside world (message bus, log, outbox, etc.).

    Requirements for implementations (infra concern):
    - at-least-once or exactly-once semantics as required
    - ordering guarantees if needed (aggregate event order)
    - durability if required (outbox pattern recommended)
    """

    def publish(self, events: tuple[BaseEvent, ...]) -> None:
        raise NotImplementedError
