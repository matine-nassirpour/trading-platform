from quantum.application.errors.application_error import ApplicationError
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.application.services.event_processing_service import EventProcessingService
from quantum.domain.shared_kernel.events.actor_id import ActorId
from quantum.domain.shared_kernel.events.causation_id import CausationId
from quantum.domain.shared_kernel.events.correlation_id import CorrelationId
from quantum.domain.shared_kernel.identifiers.order_id import OrderId
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.execution.order.order import Order
from quantum.domain.trading.execution.order.order_type import OrderType
from quantum.domain.trading.execution.order.position_side import PositionSide
from quantum.domain.trading.intent.trading_intent import TradingIntentState


class CreateOrderUseCase:

    def __init__(
        self,
        *,
        event_processing: EventProcessingService,
        uow: UnitOfWork,
    ) -> None:
        self._event_processing = event_processing
        self._uow = uow

    def execute(
        self,
        *,
        intent: TradingIntentState,
        order_id: OrderId,
        symbol: Symbol,
        order_type: OrderType,
        side: PositionSide,
        volume: PositiveVolume,
    ) -> None:

        if not intent.authorized:
            raise ApplicationError("Cannot create order from non-authorized intent")

        with self._uow:

            domain_events = Order.create(
                intent_id=intent.intent_id,
                order_id=order_id,
                symbol=symbol,
                order_type=order_type,
                side=side,
                volume=volume,
            )

            self._event_processing.process(
                events=domain_events,
                actor=ActorId("system:order_creation"),
                correlation=CorrelationId.new(),
                causation=CausationId.root(),
            )

            self._uow.commit()
