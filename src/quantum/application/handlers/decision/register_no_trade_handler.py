from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.decision.register_no_trade_command import (
    RegisterNoTradeCommand,
)
from quantum.application.handlers.command_handler import CommandHandler
from quantum.application.ports.outbound.clock import Clock
from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.id_generator import IdGenerator
from quantum.domain.decision.events.v1.no_trade_decision_event import (
    NoTradeDecisionEvent,
)
from quantum.domain.shared_kernel.events.actor_id import ActorId
from quantum.domain.shared_kernel.events.causation_id import CausationId
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_metadata import EventMetadata
from quantum.domain.shared_kernel.events.event_sequence import EventSequence


class RegisterNoTradeHandler(CommandHandler[RegisterNoTradeCommand, None]):

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

    def handle(self, command: RegisterNoTradeCommand) -> CommandResult[None]:

        event = NoTradeDecisionEvent(
            symbol=command.symbol,
            decision_identity=command.decision_identity,
            no_trade_decision=command.outcome,
        )

        envelope = EventEnvelope(
            id=self._ids.new_event_id(),
            sequence=EventSequence.initial().next(),
            occurred_at=self._clock.now_epoch_ms(),
            recorded_at=self._clock.now_epoch_ms(),
            event=event,
            metadata=EventMetadata(
                actor_id=ActorId("system:decision_engine"),
                correlation_id=self._ids.new_correlation_id(),
                causation_id=CausationId.root(),
            ),
        )

        self._store.append([envelope])
        self._bus.publish(envelope)

        return CommandResult()
