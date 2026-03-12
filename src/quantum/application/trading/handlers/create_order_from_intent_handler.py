from collections.abc import Sequence

from quantum.application.ports.outbound.transaction.outbox_repository import (
    OutboxRepository,
)
from quantum.application.ports.outbound.transaction.unit_of_work import UnitOfWork
from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.base_handlers.aggregate_existence_policy import (
    AggregateExistencePolicy,
)
from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)
from quantum.application.shared.eventing.event_enveloper import (
    ApplicationEventEnveloper,
)
from quantum.application.shared.eventing.event_sourced_repository import (
    EventSourcedRepository,
)
from quantum.application.trading.commands.create_order_from_intent_command import (
    CreateOrderFromIntentCommand,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.trading.execution.order.order import Order, OrderId
from quantum.domain.trading.execution.order.order_state_base import OrderStateBase


class CreateOrderFromIntentHandler(
    AggregateCommandHandler[
        CreateOrderFromIntentCommand,
        None,
        OrderId,
        OrderStateBase,
        Order,
    ]
):
    """
    Create an Order aggregate from an already-authorized upstream intent.
    """

    def __init__(
        self,
        *,
        repository: EventSourcedRepository[OrderId, OrderStateBase, Order],
        outbox: OutboxRepository,
        uow: UnitOfWork,
        enveloper: ApplicationEventEnveloper,
    ) -> None:
        super().__init__(
            repository=repository,
            outbox=outbox,
            uow=uow,
            enveloper=enveloper,
            existence_policy=AggregateExistencePolicy.MUST_NOT_EXIST,
        )

    def _aggregate_id(self, command: CreateOrderFromIntentCommand) -> OrderId:
        return command.order_id

    def _context(
        self,
        command: CreateOrderFromIntentCommand,
    ) -> ApplicationEventContext:
        return command.context

    def _execute_domain(
        self,
        *,
        command: CreateOrderFromIntentCommand,
        aggregate: Order,
    ) -> tuple[Sequence[BaseEvent], None]:

        domain_events = aggregate.create(
            intent_id=command.intent_id,
            broker_order_id=command.broker_order_id,
            symbol=command.symbol,
            order_type=command.order_type,
            side=command.side,
            volume=command.volume,
        )
        return domain_events, None
