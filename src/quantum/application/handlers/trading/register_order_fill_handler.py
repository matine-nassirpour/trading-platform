from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.trading.register_order_fill_command import (
    RegisterOrderFillCommand,
)
from quantum.application.errors.application_error import DomainExecutionError
from quantum.application.handlers.command_handler import AsyncCommandHandler
from quantum.application.ports.outbound.clock import Clock
from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.id_generator import IdGenerator
from quantum.application.ports.outbound.repositories.order_repository import (
    OrderRepository,
)
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.application.services.event_pipeline import persist_and_publish
from quantum.domain.shared_kernel.errors.domain_error import DomainError


class RegisterOrderFillHandler(AsyncCommandHandler[RegisterOrderFillCommand, None]):

    def __init__(
        self,
        *,
        repository: OrderRepository,
        uow: UnitOfWork,
        store: EventStore,
        bus: EventBusPort,
        clock: Clock,
        ids: IdGenerator,
    ) -> None:
        super().__init__(uow=uow, store=store, bus=bus, clock=clock, ids=ids)
        self._repository = repository

    async def handle(self, command: RegisterOrderFillCommand) -> CommandResult[None]:

        try:
            with self._uow:
                order = self._repository.load(command.order_id)

                domain_events = order.register_fill(fill=command.fill)

                await persist_and_publish(
                    stream_id=f"order-{command.order_id.value}",
                    events=domain_events,
                    store=self._store,
                    bus=self._bus,
                    ids=self._ids,
                    clock=self._clock,
                    actor="system:execution",
                )

                self._uow.commit()

            return CommandResult()

        except DomainError as error:
            raise DomainExecutionError(error) from None
