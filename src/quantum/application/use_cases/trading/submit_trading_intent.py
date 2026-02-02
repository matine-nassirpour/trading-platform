from quantum.application.dto.commands.submit_trading_intent import (
    SubmitTradingIntentCommand,
)
from quantum.application.ports.outbound.domain_event_publisher import (
    DomainEventPublisher,
)
from quantum.application.ports.outbound.trading_intent_repository import (
    TradingIntentRepository,
)
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.domain.trading.intent import TradingIntent


class SubmitTradingIntentUseCase:
    """
    Application use case responsible for submitting a new TradingIntent.

    Dependencies:
    - TradingIntentRepo : persistence of aggregate
    - EventPublisher    : transactional domain event publication
    - UoW               : atomic transaction boundary
    """

    def __init__(
        self,
        *,
        intent_repo: TradingIntentRepository,
        event_publisher: DomainEventPublisher,
        uow: UnitOfWork,
    ) -> None:
        self._intent_repo = intent_repo
        self._event_publisher = event_publisher
        self._uow = uow

    def execute(self, command: SubmitTradingIntentCommand) -> None:
        with self._uow:
            intent = TradingIntent(
                intent_id=command.intent_id,
                symbol=command.symbol,
                side=command.side,
            )

            intent = intent.submit(
                at=command.decision_epoch_ms,
                client_order_id=command.client_order_id,
            )

            self._intent_repo.save(intent)
            self._event_publisher.publish(intent.events)
            self._uow.commit()
