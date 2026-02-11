from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.trading.create_trading_intent_command import (
    CreateTradingIntentCommand,
)
from quantum.application.errors.application_error import DomainExecutionError
from quantum.application.handlers.command_handler import AsyncCommandHandler
from quantum.application.ports.outbound.clock import Clock
from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.id_generator import IdGenerator
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.application.services.event_pipeline import persist_and_publish
from quantum.domain.shared_kernel.errors.domain_error import DomainError
from quantum.domain.trading.intent.trading_intent import TradingIntent


class CreateTradingIntentHandler(AsyncCommandHandler[CreateTradingIntentCommand, None]):

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        store: EventStore,
        bus: EventBusPort,
        clock: Clock,
        ids: IdGenerator,
    ) -> None:
        super().__init__(uow=uow, store=store, bus=bus, clock=clock, ids=ids)

    async def handle(self, command: CreateTradingIntentCommand) -> CommandResult[None]:

        try:
            with self._uow:
                domain_events = TradingIntent.create(
                    intent_id=command.intent_id,
                    symbol=command.symbol,
                    side=command.side,
                    decision_identity=command.decision_identity,
                    context=command.context,
                )

                await persist_and_publish(
                    stream_id=f"intent-{command.intent_id.value}",
                    events=domain_events,
                    store=self._store,
                    bus=self._bus,
                    ids=self._ids,
                    clock=self._clock,
                    actor="system:intent",
                )

                self._uow.commit()

            return CommandResult()

        except DomainError as error:
            raise DomainExecutionError(error) from None
