from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.trading.open_position_command import (
    OpenPositionCommand,
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
from quantum.domain.trading.execution.position.position import Position


class OpenPositionHandler(AsyncCommandHandler[OpenPositionCommand, None]):

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

    async def handle(self, command: OpenPositionCommand) -> CommandResult[None]:

        try:
            with self._uow:
                domain_events = Position.open(
                    position_id=command.position_id,
                    side=command.side,
                    volume=command.volume,
                    entry_price=command.entry_price,
                )

                await persist_and_publish(
                    stream_id=f"position-{command.position_id.value}",
                    events=domain_events,
                    store=self._store,
                    bus=self._bus,
                    ids=self._ids,
                    clock=self._clock,
                    actor="system:position",
                )

                self._uow.commit()

            return CommandResult()

        except DomainError as error:
            raise DomainExecutionError(error) from None
