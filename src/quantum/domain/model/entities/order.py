from __future__ import annotations

from dataclasses import dataclass, replace

from quantum.domain.model.exceptions.order_exceptions import (
    OrderAlreadyAcknowledged,
    OrderNotFillable,
)
from quantum.domain.model.exceptions.validation_exceptions import InvalidStateTransition
from quantum.domain.model.value_objects.identifiers import OrderId
from quantum.domain.model.value_objects.volume import NonNegativeVolume, PositiveVolume
from quantum.domain.types.order_status import OrderStatus


@dataclass(frozen=True, eq=False)
class Order:
    """
    Entity representing an order.
    """

    order_id: OrderId
    requested_volume: PositiveVolume
    filled_volume: NonNegativeVolume
    status: OrderStatus

    def __post_init__(self) -> None:
        self._validate()

    # --- Invariants -----------------------------------------------------------

    def _validate(self) -> None:
        if self.filled_volume.value > self.requested_volume.value:
            raise InvalidStateTransition("Filled volume cannot exceed requested volume")

        if (
            self.status == OrderStatus.FILLED
            and self.filled_volume.value != self.requested_volume.value
        ):
            raise InvalidStateTransition("FILLED order must have fully filled volume")

    # --- State transitions ----------------------------------------------------

    def acknowledge(self) -> Order:
        if self.status != OrderStatus.PENDING:
            raise OrderAlreadyAcknowledged("Only pending orders can be acknowledged")
        return replace(self, status=OrderStatus.ACKED)

    def register_fill(self, volume: PositiveVolume) -> Order:
        if self.status not in {
            OrderStatus.ACKED,
            OrderStatus.PARTIALLY_FILLED,
        }:
            raise OrderNotFillable("Order not fillable")

        new_filled = NonNegativeVolume(self.filled_volume.value + volume.value)

        status = (
            OrderStatus.FILLED
            if new_filled.value == self.requested_volume.value
            else OrderStatus.PARTIALLY_FILLED
        )

        return replace(
            self,
            filled_volume=new_filled,
            status=status,
        )
