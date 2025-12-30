from __future__ import annotations

from dataclasses import dataclass, replace

from quantum.domain.model.exceptions.order_exceptions import (
    OrderNotFillable,
    OrderOverfill,
)
from quantum.domain.model.exceptions.validation_exceptions import InvalidStateTransition
from quantum.domain.model.value_objects.identifiers import OrderId
from quantum.domain.model.value_objects.volume import NonNegativeVolume, PositiveVolume
from quantum.domain.types.order_status import OrderStatus


@dataclass(frozen=True, eq=False)
class Order:
    """
    Entity representing an order.

    Identity:
    - OrderId
    """

    order_id: OrderId
    requested_volume: PositiveVolume
    filled_volume: NonNegativeVolume
    status: OrderStatus

    # ---  Identity semantics --------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Order):
            return False
        return self.order_id == other.order_id

    def __hash__(self) -> int:
        return hash(self.order_id)

    # --- Invariants -----------------------------------------------------------

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        # volume coherence
        if self.filled_volume.value > self.requested_volume.value:
            raise InvalidStateTransition("Filled volume cannot exceed requested volume")

        # terminal state consistency
        if self.status == OrderStatus.FILLED:
            if self.filled_volume.value != self.requested_volume.value:
                raise InvalidStateTransition(
                    "FILLED order must have fully filled volume"
                )

        if self.status in {OrderStatus.REJECTED, OrderStatus.CANCELLED}:
            if self.filled_volume.value != 0:
                raise InvalidStateTransition(
                    "Rejected or cancelled order must have zero filled volume"
                )

    # --- Domain behavior ------------------------------------------------------

    def is_fillable(self) -> bool:
        """
        Orders are fillable as long as they are not terminal.
        """
        return self.status in {
            OrderStatus.PENDING,
            OrderStatus.PARTIALLY_FILLED,
        }

    def register_fill(self, volume: PositiveVolume) -> Order:
        """
        Registers a fill on the order.

        Rules:
        - Only fillable orders can accept fills
        - Overfills are forbidden
        - State transitions are implicit and deterministic
        """
        if not self.is_fillable():
            raise OrderNotFillable(
                f"Order {self.order_id} not fillable in state {self.status}"
            )

        new_total = self.filled_volume.value + volume.value

        if new_total > self.requested_volume.value:
            raise OrderOverfill(
                f"Fill {volume.value} exceeds remaining volume "
                f"({self.requested_volume.value - self.filled_volume.value})"
            )

        new_filled = NonNegativeVolume(new_total)

        new_status = (
            OrderStatus.FILLED
            if new_filled.value == self.requested_volume.value
            else OrderStatus.PARTIALLY_FILLED
        )

        return replace(
            self,
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
