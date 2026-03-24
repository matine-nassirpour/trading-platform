from dataclasses import dataclass

from quantum.domain.market.instrument.symbol import Symbol
from quantum.domain.market.value_objects.position_side import PositionSide
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.trading.execution.order.order_state_base import OrderStateBase
from quantum.domain.trading.execution.order.order_status import OrderStatus
from quantum.domain.trading.execution.order.order_type import OrderType
from quantum.domain.trading.identifiers.broker_order_id import BrokerOrderId
from quantum.domain.trading.value_objects.volume import (
    NonNegativeVolume,
    PositiveVolume,
)


@dataclass(frozen=True, slots=True)
class OrderInitializedState(OrderStateBase):
    """
    Fully initialized immutable Order aggregate state.
    """

    broker_order_id: BrokerOrderId
    symbol: Symbol

    order_type: OrderType
    side: PositionSide

    requested_volume: PositiveVolume
    filled_volume: NonNegativeVolume

    status: OrderStatus

    def _validate_types(self) -> None:
        if not isinstance(self.broker_order_id, BrokerOrderId):
            raise InvariantViolation("OrderInitializedState.broker_order_id invalid")

        if not isinstance(self.symbol, Symbol):
            raise InvariantViolation("OrderInitializedState.symbol invalid")

        if not isinstance(self.order_type, OrderType):
            raise InvariantViolation("OrderInitializedState.order_type invalid")

        if not isinstance(self.side, PositionSide):
            raise InvariantViolation("OrderInitializedState.side invalid")

        if not isinstance(self.requested_volume, PositiveVolume):
            raise InvariantViolation("OrderInitializedState.requested_volume invalid")

        if not isinstance(self.filled_volume, NonNegativeVolume):
            raise InvariantViolation("OrderInitializedState.filled_volume invalid")

        if not isinstance(self.status, OrderStatus):
            raise InvariantViolation("OrderInitializedState.status invalid")

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
