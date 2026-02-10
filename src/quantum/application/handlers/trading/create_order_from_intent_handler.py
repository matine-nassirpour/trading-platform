from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.trading.create_order_from_intent_command import (
    CreateOrderFromIntentCommand,
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
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.trading.execution.order.order import Order


class CreateOrderFromIntentHandler(CommandHandler[CreateOrderFromIntentCommand, None]):

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

    def handle(self, command: CreateOrderFromIntentCommand) -> CommandResult[None]:

        events = Order.create(
            intent_id=command.intent_id,
            order_id=command.order_id,
            symbol=command.symbol,
            order_type=command.order_type,
            side=command.side,
            volume=command.volume,
        )

        envelopes = [
            EventEnvelope(
                id=self._ids.new_event_id(),
                sequence=EventSequence.initial().next(),
                occurred_at=self._clock.now_epoch_ms(),
                recorded_at=self._clock.now_epoch_ms(),
                event=e,
                metadata=EventMetadata(
                    actor_id=ActorId("system:order"),
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
