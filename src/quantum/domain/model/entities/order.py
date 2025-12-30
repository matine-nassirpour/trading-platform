from __future__ import annotations

from dataclasses import dataclass, replace

from quantum.domain.model.exceptions.order_exceptions import (
    OrderNotFillable,
    OrderOverfill,
)
from quantum.domain.model.exceptions.validation_exceptions import InvalidStateTransition
from quantum.domain.model.value_objects.fill import Fill
from quantum.domain.model.value_objects.identifiers import OrderId
from quantum.domain.model.value_objects.volume import NonNegativeVolume, PositiveVolume
from quantum.domain.types.enums import OrderType
from quantum.domain.types.order_status import OrderStatus
from quantum.domain.types.position_side import PositionSide


@dataclass(frozen=True, eq=False)
class Order:
    """
    Entity representing an order.

    Identity:
    - OrderId
    """

    order_id: OrderId
    order_type: OrderType
    side: PositionSide

    requested_volume: PositiveVolume
    filled_volume: NonNegativeVolume

    fills: tuple[Fill, ...]
    status: OrderStatus

    # ---  Identity semantics --------------------------------------------------

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Order) and self.order_id == other.order_id

    def __hash__(self) -> int:
        return hash(self.order_id)

    # --- Invariants -----------------------------------------------------------

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if not isinstance(self.fills, tuple):
            raise InvalidStateTransition("Fills must be stored as an immutable tuple")

        total_filled = sum(f.volume.value for f in self.fills)

        if total_filled != self.filled_volume.value:
            raise InvalidStateTransition("Filled volume must equal sum of fills")

        if self.filled_volume.value > self.requested_volume.value:
            raise InvalidStateTransition("Filled volume cannot exceed requested volume")

        if self.status == OrderStatus.FILLED:
            if self.filled_volume.value != self.requested_volume.value:
                raise InvalidStateTransition("FILLED order must be fully filled")

    # --- Domain behavior ------------------------------------------------------

    def is_fillable(self) -> bool:
        """
        Orders are fillable as long as they are not terminal.
        """
        return self.status in {
            OrderStatus.PENDING,
            OrderStatus.PARTIALLY_FILLED,
        }

    def register_fill(self, fill: Fill) -> Order:
        """
        Registers a fill on the order.

        Rules:
        - Only fillable orders can accept fills
        - Overfills are forbidden
        - State transitions are implicit and deterministic
        """
        if not self.is_fillable():
            raise OrderNotFillable(f"Order {self.order_id} not fillable")

        new_total = self.filled_volume.value + fill.volume.value

        if new_total > self.requested_volume.value:
            raise OrderOverfill("Fill exceeds remaining volume")

        new_filled = NonNegativeVolume(new_total)

        new_status = (
            OrderStatus.FILLED
            if new_filled.value == self.requested_volume.value
            else OrderStatus.PARTIALLY_FILLED
        )

        return replace(
            self,
            fills=self.fills + (fill,),
            filled_volume=new_filled,
            status=new_status,
        )

    def cancel(self) -> Order:
        """
        Cancels an order if it is not terminal.

        Note:
        - Partial fills are NOT reverted.
        """
        if self.status in {
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
        }:
            raise InvalidStateTransition(f"Cannot cancel order in state {self.status}")

        return replace(self, status=OrderStatus.CANCELLED)
