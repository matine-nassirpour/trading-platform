from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.risk.register_pnl_command import RegisterPnLCommand
from quantum.application.errors.application_error import DomainExecutionError
from quantum.application.handlers.command_handler import AsyncCommandHandler
from quantum.application.ports.outbound.clock import Clock
from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.id_generator import IdGenerator
from quantum.application.ports.outbound.repositories.risk_repository import (
    RiskRepository,
)
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.application.services.event_pipeline import persist_and_publish
from quantum.domain.shared_kernel.errors.domain_error import DomainError


class RegisterPnLHandler(AsyncCommandHandler[RegisterPnLCommand, None]):

    def __init__(
        self,
        *,
        repository: RiskRepository,
        uow: UnitOfWork,
        store: EventStore,
        bus: EventBusPort,
        clock: Clock,
        ids: IdGenerator,
    ) -> None:
        super().__init__(uow=uow, store=store, bus=bus, clock=clock, ids=ids)
        self._repository = repository

    async def handle(self, command: RegisterPnLCommand) -> CommandResult[None]:

        try:
            with self._uow:
                aggregate = self._repository.load()

                domain_events = aggregate.register_pnl(
                    pnl=command.pnl,
                    drawdown=command.drawdown,
                    daily_loss=command.daily_loss,
                    exposure=command.exposure,
                    notional=command.notional,
                )

                await persist_and_publish(
                    stream_id="risk-state",
                    events=domain_events,
                    store=self._store,
                    bus=self._bus,
                    ids=self._ids,
                    clock=self._clock,
                    actor="system:risk_engine",
                )

                self._uow.commit()

            return CommandResult()

        except DomainError as error:
            raise DomainExecutionError(error) from None
