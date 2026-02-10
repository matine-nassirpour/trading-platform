from quantum.application.errors.application_error import ApplicationError
from quantum.application.ports.outbound.repositories.order_repository import (
    OrderRepository,
)
from quantum.application.ports.outbound.repositories.trading_intent_repository import (
    TradingIntentRepository,
)
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.application.services.execution_routing_service import (
    ExecutionRoutingService,
)
from quantum.application.use_cases.order.create_order_use_case import CreateOrderUseCase
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.identifiers.order_id import OrderId
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.execution.order.order_type import OrderType
from quantum.domain.trading.execution.order.position_side import PositionSide


class PlaceOrderUseCase:
    """
    High-level orchestration use case.

    Responsibilities:
    - Take an AUTHORIZED TradingIntent
    - Materialize it into a domain Order
    - Route it to execution
    - Ensure idempotence and consistency
    """

    def __init__(
        self,
        *,
        intent_repository: TradingIntentRepository,
        order_repository: OrderRepository,
        create_order_use_case: CreateOrderUseCase,
        routing_service: ExecutionRoutingService,
        uow: UnitOfWork,
    ) -> None:

        self._intent_repository = intent_repository
        self._order_repository = order_repository
        self._create_order_use_case = create_order_use_case
        self._routing_service = routing_service
        self._uow = uow

    def execute(
        self,
        *,
        intent_id: IntentId,
        order_id: OrderId,
        symbol: Symbol,
        order_type: OrderType,
        side: PositionSide,
        volume: PositiveVolume,
    ) -> None:
        """
        Executes the full lifecycle:

        TradingIntent (authorized)
            → Domain Order creation
            → Execution routing
        """

        with self._uow:

            # --- 1. Load intent
            intent = self._intent_repository.load(intent_id)

            if intent is None:
                raise ApplicationError(f"TradingIntent not found: {intent_id}")

            state = intent.state

            # --- 2. Validate decision state
            if not state.authorized:
                raise ApplicationError(
                    f"Cannot place order from non-authorized intent: {intent_id}"
                )

            if state.rejected:
                raise ApplicationError(
                    f"Cannot place order from rejected intent: {intent_id}"
                )

            # --- 3. Idempotence guard
            existing = self._safe_load_order(order_id)
            if existing is not None:
                # Order already exists → assume already processed
                # Idempotent behavior: do not recreate, just ensure routing
                self._routing_service.route(intent_id)
                return

            # --- 4. Create Order (Domain materialization)
            self._create_order_use_case.execute(
                intent=state,
                order_id=order_id,
                symbol=symbol,
                order_type=order_type,
                side=side,
                volume=volume,
            )

            # --- 5. Route to execution
            self._routing_service.route(intent_id)

            # --- 6. Commit atomic unit
            self._uow.commit()

    def _safe_load_order(self, order_id: OrderId):
        """
        Defensive load to support idempotence.
        """

        try:
            return self._order_repository.load(order_id)
        except Exception:
            return None
