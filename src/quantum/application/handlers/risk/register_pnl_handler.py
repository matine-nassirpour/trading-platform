from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.risk.register_pnl_command import RegisterPnLCommand
from quantum.application.handlers.command_handler import CommandHandler
from quantum.application.ports.outbound.clock import Clock
from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.id_generator import IdGenerator
from quantum.application.ports.outbound.repositories.risk_repository import (
    RiskRepository,
)
from quantum.domain.shared_kernel.events.actor_id import ActorId
from quantum.domain.shared_kernel.events.causation_id import CausationId
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_metadata import EventMetadata
from quantum.domain.shared_kernel.events.event_sequence import EventSequence


class RegisterPnLHandler(CommandHandler[RegisterPnLCommand, None]):

    def __init__(
        self,
        *,
        repository: RiskRepository,
        store: EventStore,
        bus: EventBusPort,
        clock: Clock,
        ids: IdGenerator,
    ) -> None:
        self._repository = repository
        self._store = store
        self._bus = bus
        self._clock = clock
        self._ids = ids

    def handle(self, command: RegisterPnLCommand) -> CommandResult[None]:

        aggregate = self._repository.load()

        events = aggregate.register_pnl(
            pnl=command.pnl,
            drawdown=command.drawdown,
            daily_loss=command.daily_loss,
            exposure=command.exposure,
            notional=command.notional,
        )

        envelopes = [
            EventEnvelope(
                id=self._ids.new_event_id(),
                sequence=EventSequence.initial().next(),
                occurred_at=self._clock.now_epoch_ms(),
                recorded_at=self._clock.now_epoch_ms(),
                event=e,
                metadata=EventMetadata(
                    actor_id=ActorId("system:risk_engine"),
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
