from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.identifiers.order_id import OrderId
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.shared_kernel.value_objects.volume import (
    NonNegativeVolume,
    PositiveVolume,
)
from quantum.domain.trading.execution.order.order_state_base import OrderStateBase
from quantum.domain.trading.execution.order.order_status import OrderStatus
from quantum.domain.trading.execution.order.order_type import OrderType
from quantum.domain.trading.execution.order.position_side import PositionSide


@dataclass(frozen=True, slots=True)
class OrderInitializedState(OrderStateBase):

    order_id: OrderId
    symbol: Symbol

    order_type: OrderType
    side: PositionSide

    requested_volume: PositiveVolume
    filled_volume: NonNegativeVolume

    status: OrderStatus

    def _validate(self):
        if self.last_sequence.is_initial():
            raise InvariantViolation("Initialized order cannot be initial")

        if self.filled_volume.value > self.requested_volume.value:
            raise InvariantViolation("Overfill")
