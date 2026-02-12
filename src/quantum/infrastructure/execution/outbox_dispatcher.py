from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.application.ports.outbound.outbox_repository import OutboxRepository


class OutboxDispatcher:

    def __init__(
        self,
        outbox: OutboxRepository,
        bus: EventBusPort,
    ) -> None:
        self._outbox = outbox
        self._bus = bus
        self._running = False

    async def dispatch_pending(self) -> None:
        events = self._outbox.collect_unpublished()

        if not events:
            return

        await self._bus.publish_many(events)
        self._outbox.mark_as_published(events)
