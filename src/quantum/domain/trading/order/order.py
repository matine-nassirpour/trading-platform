from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal

from quantum.domain.execution.value_objects.fill import Fill
from quantum.domain.shared.errors.invariants import InvalidStateTransition
from quantum.domain.shared.errors.order_errors import OrderNotFillable, OrderOverfill
from quantum.domain.trading.types.order_status import OrderStatus
from quantum.domain.trading.types.order_type import OrderType
from quantum.domain.trading.types.position_side import PositionSide
from quantum.domain.trading.value_objects.identifiers import OrderId
from quantum.domain.trading.value_objects.volume import (
    NonNegativeVolume,
    PositiveVolume,
)


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
    fills: tuple[Fill, ...]
    status: OrderStatus

    # ---  Identity semantics --------------------------------------------------

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Order) and self.order_id == other.order_id

    def __hash__(self) -> int:
        return hash(self.order_id)

    # --- Properties  ----------------------------------------------------------

    @property
    def filled_volume(self) -> NonNegativeVolume:
        """
        Canonical filled volume, derived from fills.

        This is the ONLY source of truth.
        """
        total = sum(
            (fill.volume.value for fill in self.fills),
            start=Decimal("0"),
        )
        return NonNegativeVolume(total)

    @property
    def remaining_volume(self) -> NonNegativeVolume:
        """
        Remaining executable volume.
        """
        remaining = self.requested_volume.value - self.filled_volume.value
        return NonNegativeVolume(remaining)

    # --- Invariants -----------------------------------------------------------

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if not isinstance(self.fills, tuple):
            raise InvalidStateTransition("Fills must be stored as an immutable tuple")

        if self.filled_volume.value > self.requested_volume.value:
            raise InvalidStateTransition(
                "Total filled volume cannot exceed requested volume"
            )

        if self.status == OrderStatus.FILLED:
            if self.remaining_volume.value != Decimal("0"):
                raise InvalidStateTransition(
                    "FILLED order must have zero remaining volume"
                )

        if self.status == OrderStatus.PENDING:
            if self.fills:
                raise InvalidStateTransition("PENDING order must not contain fills")

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

        if fill.volume.value > self.remaining_volume.value:
            raise OrderOverfill("Fill exceeds remaining order volume")

        new_fills = self.fills + (fill,)

        new_status = (
            OrderStatus.FILLED
            if fill.volume.value == self.remaining_volume.value
            else OrderStatus.PARTIALLY_FILLED
        )

        return replace(
            self,
            fills=new_fills,
            status=new_status,
        )

    def cancel(self) -> Order:
        """
        Cancels an order if it is not terminal.

        Notes:
        - Partial fills are NOT reverted
        - Cancellation is final
        """
        if self.status in {
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
        }:
            raise InvalidStateTransition(f"Cannot cancel order in state {self.status}")

        return replace(self, status=OrderStatus.CANCELLED)
