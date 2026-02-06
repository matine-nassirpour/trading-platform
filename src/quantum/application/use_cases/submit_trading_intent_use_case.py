from quantum.application.commands.submit_trading_intent_command import (
    SubmitTradingIntentCommand,
)
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.application.services.event_processing_service import EventProcessingService
from quantum.domain.shared_kernel.events.actor_id import ActorId
from quantum.domain.shared_kernel.events.causation_id import CausationId
from quantum.domain.shared_kernel.events.correlation_id import CorrelationId
from quantum.domain.trading.intent.trading_intent import TradingIntent


class SubmitTradingIntentUseCase:

    def __init__(
        self,
        *,
        event_processing: EventProcessingService,
        uow: UnitOfWork,
    ) -> None:
        self._event_processing = event_processing
        self._uow = uow

    def execute(self, command: SubmitTradingIntentCommand) -> None:

        with self._uow:

            domain_events = TradingIntent.create(
                intent_id=command.intent_id,
                decision_identity=command.decision_identity,
                context=command.trading_context,
            )

            self._event_processing.process(
                events=domain_events,
                actor=ActorId("system:intent"),
                correlation=CorrelationId.new(),
                causation=CausationId.root(),
            )

            self._uow.commit()
