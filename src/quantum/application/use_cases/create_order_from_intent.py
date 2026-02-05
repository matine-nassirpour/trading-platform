from quantum.application.commands.create_order_from_intent import (
    CreateOrderFromIntentCommand,
)
from quantum.application.errors.not_found_errors import TradingIntentNotFound
from quantum.application.ports.outbound.domain_event_publisher import EventPublisher
from quantum.application.ports.outbound.trading_intent_repository import (
    TradingIntentRepository,
)
from quantum.application.ports.outbound.unit_of_work import UnitOfWork


class CreateOrderFromIntentUseCase:
    """
    Creates an Order inside an already submitted TradingIntent.
    """

    def __init__(
        self,
        *,
        intent_repo: TradingIntentRepository,
        event_publisher: EventPublisher,
        uow: UnitOfWork,
    ) -> None:
        self._intent_repo = intent_repo
        self._event_publisher = event_publisher
        self._uow = uow

    def execute(self, command: CreateOrderFromIntentCommand) -> None:
        with self._uow:
            intent = self._intent_repo.get(command.intent_id)
            if intent is None:
                raise TradingIntentNotFound(command.intent_id)

            intent = intent.create_order(
                order_id=command.order_id,
                order_type=command.order_type,
                volume=command.volume,
                at=command.at,
                sizing_model=command.sizing_model,
            )

            self._intent_repo.save(intent)
            self._event_publisher.publish(intent.events)
            self._uow.commit()
