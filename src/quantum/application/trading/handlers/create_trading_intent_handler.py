from collections.abc import Iterable

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
from quantum.application.trading.commands.create_trading_intent_command import (
    CreateTradingIntentCommand,
)
from quantum.domain.decision.trading_intent.trading_intent import TradingIntent
from quantum.domain.decision.trading_intent.trading_intent_state_base import (
    TradingIntentStateBase,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId


class CreateTradingIntentHandler(
    AggregateCommandHandler[
        CreateTradingIntentCommand,
        None,
        IntentId,
        TradingIntentStateBase,
        TradingIntent,
    ]
):
    """
    Creates a new TradingIntent aggregate.
    """

    def __init__(
        self,
        *,
        repository: EventSourcedRepository[
            IntentId, TradingIntentStateBase, TradingIntent
        ],
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

    def _aggregate_id(self, command: CreateTradingIntentCommand) -> IntentId:
        return command.intent_id

    def _context(
        self,
        command: CreateTradingIntentCommand,
    ) -> ApplicationEventContext:
        return command.context

    def _execute_domain(
        self,
        *,
        command: CreateTradingIntentCommand,
        aggregate: TradingIntent,
    ) -> tuple[Iterable[BaseEvent], None]:

        _, domain_events = TradingIntent.create_new(
            aggregate_id=command.intent_id,
            symbol=command.symbol,
            side=command.side,
            decision_identity=command.decision_identity,
            context=command.trading_context,
        )

        return domain_events, None
