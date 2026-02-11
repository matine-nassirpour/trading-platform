from quantum.application.commands.command_result import CommandResult
from quantum.application.commands.trading.create_order_from_intent_command import (
    CreateOrderFromIntentCommand,
)
from quantum.application.errors.application_error import (
    DomainExecutionError,
    UseCaseError,
)
from quantum.application.handlers.command_handler import AsyncCommandHandler
from quantum.application.ports.outbound.clock import Clock
from quantum.application.ports.outbound.event_bus_port import EventBusPort
from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.id_generator import IdGenerator
from quantum.application.ports.outbound.repositories.trading_intent_repository import (
    TradingIntentRepository,
)
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.application.services.event_pipeline import persist_and_publish
from quantum.domain.shared_kernel.errors.domain_error import DomainError
from quantum.domain.trading.execution.order.order import Order


class CreateOrderFromIntentHandler(
    AsyncCommandHandler[CreateOrderFromIntentCommand, None]
):

    def __init__(
        self,
        *,
        repository: TradingIntentRepository,
        uow: UnitOfWork,
        store: EventStore,
        bus: EventBusPort,
        clock: Clock,
        ids: IdGenerator,
    ) -> None:
        super().__init__(uow=uow, store=store, bus=bus, clock=clock, ids=ids)
        self._repository = repository

    async def handle(
        self, command: CreateOrderFromIntentCommand
    ) -> CommandResult[None]:

        try:
            with self._uow:
                intent = self._repository.load(command.intent_id)

                if not intent.state.authorized:
                    raise UseCaseError("Cannot create order from non-authorized intent")

                domain_events = Order.create(
                    intent_id=command.intent_id,
                    order_id=command.order_id,
                    symbol=command.symbol,
                    order_type=command.order_type,
                    side=command.side,
                    volume=command.volume,
                )

                await persist_and_publish(
                    stream_id=f"order-{command.order_id.value}",
                    events=domain_events,
                    store=self._store,
                    bus=self._bus,
                    ids=self._ids,
                    clock=self._clock,
                    actor="system:order",
                )

                self._uow.commit()

            return CommandResult()

        except DomainError as error:
            raise DomainExecutionError(error) from None
