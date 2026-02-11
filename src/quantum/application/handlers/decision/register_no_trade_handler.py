from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.decision.register_no_trade_command import (
    RegisterNoTradeCommand,
)
from quantum.application.errors.application_error import DomainExecutionError
from quantum.application.handlers.command_handler import AsyncCommandHandler
from quantum.application.ports.outbound.clock import Clock
from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.id_generator import IdGenerator
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.application.services.event_pipeline import persist_and_publish
from quantum.domain.decision.events.v1.no_trade_decision_event import (
    NoTradeDecisionEvent,
)
from quantum.domain.shared_kernel.errors.domain_error import DomainError


class RegisterNoTradeHandler(AsyncCommandHandler[RegisterNoTradeCommand, None]):

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

    async def handle(self, command: RegisterNoTradeCommand) -> CommandResult[None]:

        try:
            with self._uow:
                domain_events = [
                    NoTradeDecisionEvent(
                        symbol=command.symbol,
                        decision_identity=command.decision_identity,
                        no_trade_decision=command.outcome,
                    )
                ]

                await persist_and_publish(
                    stream_id=(
                        f"decision-{command.decision_identity.strategy_id.value}"
                    ),
                    events=domain_events,
                    store=self._store,
                    bus=self._bus,
                    ids=self._ids,
                    clock=self._clock,
                    actor="system:decision_engine",
                )

                self._uow.commit()

            return CommandResult()

        except DomainError as error:
            raise DomainExecutionError(error) from None
