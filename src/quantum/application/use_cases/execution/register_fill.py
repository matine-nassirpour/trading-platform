from quantum.application.dto.commands.register_fill import RegisterFillCommand
from quantum.application.errors.not_found_errors import TradingIntentNotFound
from quantum.application.mappers.fill_event_mapper import FillIntegrationEventMapper
from quantum.application.ports.outbound.integration_event_publisher import (
    IntegrationEventPublisher,
)
from quantum.application.ports.outbound.trading_intent_repository import (
    TradingIntentRepository,
)
from quantum.application.ports.outbound.unit_of_work import UnitOfWork


class RegisterFillUseCase:
    def __init__(
        self,
        *,
        intent_repo: TradingIntentRepository,
        event_publisher: IntegrationEventPublisher,
        uow: UnitOfWork,
    ) -> None:
        self._intent_repo = intent_repo
        self._event_publisher = event_publisher
        self._uow = uow

    def execute(self, command: RegisterFillCommand) -> None:
        with self._uow:
            intent = self._intent_repo.get(command.intent_id)
            if intent is None:
                raise TradingIntentNotFound(command.intent_id)

            intent = intent.register_fill(
                order_id=command.order_id,
                fill=command.fill,
            )

            self._intent_repo.save(intent)

            integration_events = (
                FillIntegrationEventMapper.from_fill(
                    intent_id=command.intent_id,
                    order_id=command.order_id,
                    fill=command.fill,
                ),
            )

            self._event_publisher.publish(integration_events)
            self._uow.commit()
