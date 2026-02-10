from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.trading.register_order_fill_command import (
    RegisterOrderFillCommand,
)
from quantum.application.handlers.command_handler import CommandHandler
from quantum.application.ports.outbound.clock import Clock
from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.id_generator import IdGenerator
from quantum.domain.shared_kernel.events.actor_id import ActorId
from quantum.domain.shared_kernel.events.causation_id import CausationId
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_metadata import EventMetadata
from quantum.domain.trading.execution.order.order import Order


class RegisterOrderFillHandler(CommandHandler[RegisterOrderFillCommand, None]):

    def __init__(
        self,
        *,
        store: EventStore,
        bus: EventBusPort,
        clock: Clock,
        ids: IdGenerator,
    ) -> None:
        self._store = store
        self._bus = bus
        self._clock = clock
        self._ids = ids

    def handle(self, command: RegisterOrderFillCommand) -> CommandResult[None]:

        stream = f"order-{command.order_id}"
        history = self._store.load_stream(stream)

        order = Order.rehydrate(history)

        events = order.register_fill(fill=command.fill)

        envelopes = [
            EventEnvelope(
                id=self._ids.new_event_id(),
                sequence=history[-1].sequence.next(),
                occurred_at=self._clock.now_epoch_ms(),
                recorded_at=self._clock.now_epoch_ms(),
                event=e,
                metadata=EventMetadata(
                    actor_id=ActorId("system:execution"),
                    correlation_id=self._ids.new_correlation_id(),
                    causation_id=CausationId.root(),
                ),
            )
            for e in events
        ]

        self._store.append(envelopes)

        for env in envelopes:
            self._bus.publish(env)

        return CommandResult()
