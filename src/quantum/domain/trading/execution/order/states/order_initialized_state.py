from dataclasses import dataclass

from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.market.instrument.pricing.reference_price import ReferencePrice
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.monetary.price import Price
from quantum.domain.trading.execution.order.order_kind import OrderKind
from quantum.domain.trading.execution.order.order_status import OrderStatus
from quantum.domain.trading.execution.order.states.order_state_base import (
    OrderStateBase,
)
from quantum.domain.trading.execution.order.time_in_force import TimeInForce
from quantum.domain.trading.execution.position_side import PositionSide
from quantum.domain.trading.identity.broker_order_ref import BrokerOrderRef
from quantum.domain.trading.value_objects.volume import (
    NonNegativeVolume,
    PositiveVolume,
)


@dataclass(frozen=True, slots=True)
class OrderInitializedState(OrderStateBase):
    """
    Fully initialized immutable Order aggregate state.
    """

    broker_order_ref: BrokerOrderRef
    symbol: Symbol

    order_kind: OrderKind
    side: PositionSide

    requested_volume: PositiveVolume
    filled_volume: NonNegativeVolume

    status: OrderStatus

    intent_id: DecisionId

    reference_price: ReferencePrice | None
    stop_price: Price | None
    limit_price: Price | None

    sl: Price | None
    tp: Price | None

    time_in_force: TimeInForce

    def _validate_types(self) -> None:
        required_fields: tuple[tuple[str, object, type[object]], ...] = (
            ("broker_order_ref", self.broker_order_ref, BrokerOrderRef),
            ("symbol", self.symbol, Symbol),
            ("order_kind", self.order_kind, OrderKind),
            ("side", self.side, PositionSide),
            ("requested_volume", self.requested_volume, PositiveVolume),
            ("filled_volume", self.filled_volume, NonNegativeVolume),
            ("status", self.status, OrderStatus),
            ("intent_id", self.intent_id, DecisionId),
            ("time_in_force", self.time_in_force, TimeInForce),
        )

        optional_fields: tuple[tuple[str, object, type[object]], ...] = (
            ("reference_price", self.reference_price, ReferencePrice),
            ("stop_price", self.stop_price, Price),
            ("limit_price", self.limit_price, Price),
            ("sl", self.sl, Price),
            ("tp", self.tp, Price),
        )

        for field_name, value, expected_type in required_fields:
            if not isinstance(value, expected_type):
                raise InvariantViolation(f"OrderInitializedState.{field_name} invalid")

        for field_name, value, expected_type in optional_fields:
            if value is not None and not isinstance(value, expected_type):
                raise InvariantViolation(f"OrderInitializedState.{field_name} invalid")

    def _assert_status_consistency(self) -> None:
        if (
            self.status.is_filled()
            and self.filled_volume.value != self.requested_volume.value
        ):
            raise InvariantViolation("Filled order must be fully filled")

        if self.status.is_partially_filled():
            if self.filled_volume.value == 0:
                raise InvariantViolation("Partially filled order cannot be 0")

            if self.filled_volume.value == self.requested_volume.value:
                raise InvariantViolation(
                    "Partially filled order cannot be fully filled"
                )

        if self.status.is_pending() and self.filled_volume.value != 0:
            raise InvariantViolation("Pending order cannot have filled volume")

        if (
            self.status.is_cancelled()
            and self.filled_volume.value == self.requested_volume.value
        ):
            raise InvariantViolation("Cancelled order cannot be fully filled")

    def _validate_semantics(self) -> None:
        super()._validate_semantics()
        self._validate_types()

        if self.last_sequence.is_initial():
            raise InvariantViolation("Initialized order cannot be initial")

        if self.filled_volume.value > self.requested_volume.value:
            raise InvariantViolation("Overfill")

        self._assert_status_consistency()
