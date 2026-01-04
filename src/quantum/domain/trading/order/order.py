from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal

from quantum.domain.execution.value_objects.execution_fill import ExecutionFill
from quantum.domain.shared_kernel.errors.invariants import InvalidStateTransition
from quantum.domain.shared_kernel.errors.order_errors import (
    OrderNotFillable,
    OrderOverfill,
)
from quantum.domain.shared_kernel.value_objects.volume import (
    NonNegativeVolume,
    PositiveVolume,
)
from quantum.domain.trading.value_objects.identifiers.order_id import OrderId
from quantum.domain.trading.value_objects.order.order_status import OrderStatus
from quantum.domain.trading.value_objects.order.order_type import OrderType
from quantum.domain.trading.value_objects.order.position_side import PositionSide


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
    fills: tuple[ExecutionFill, ...]
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

    def _validate(self) -> None:
        self._validate_fills_container()
        self._validate_fills_types()
        self._validate_volume_consistency()
        self._validate_filled_state()
        self._validate_pending_state()

    def _validate_fills_container(self) -> None:
        if not isinstance(self.fills, tuple):
            raise InvalidStateTransition(
                "Execution fills must be stored as an immutable tuple"
            )

    def _validate_fills_types(self) -> None:
        for fill in self.fills:
            if not isinstance(fill, ExecutionFill):
                raise InvalidStateTransition(
                    "Order may only contain ExecutionFill instances"
                )

    def _validate_volume_consistency(self) -> None:
        if self.filled_volume.value > self.requested_volume.value:
            raise InvalidStateTransition(
                "Total filled volume cannot exceed requested volume"
            )

    def _validate_filled_state(self) -> None:
        if self.status.is_filled():
            if self.remaining_volume.value != Decimal("0"):
                raise InvalidStateTransition(
                    "FILLED order must have zero remaining volume"
                )

    def _validate_pending_state(self) -> None:
        if self.status.is_pending() and self.fills:
            raise InvalidStateTransition(
                "PENDING order must not contain execution fills"
            )

    # --- Domain behavior ------------------------------------------------------

    def is_fillable(self) -> bool:
        """
        Orders are fillable as long as they are not terminal.
        """
        return self.status.is_fillable()

    def register_fill(self, fill: ExecutionFill) -> Order:
        """
        Registers a fill on the order.
        """
        if not self.is_fillable():
            raise OrderNotFillable(f"Order {self.order_id} not fillable")

        if fill.volume.value > self.remaining_volume.value:
            raise OrderOverfill("Execution fill exceeds remaining order volume")

        new_fills = self.fills + (fill,)

        new_status = (
            OrderStatus.filled()
            if fill.volume.value == self.remaining_volume.value
            else OrderStatus.partially_filled()
        )

        return replace(
            self,
            fills=new_fills,
            status=new_status,
        )

    def cancel(self) -> Order:
        """
        Cancels an order if it is not terminal.
        """
        if self.status.is_terminal():
            raise InvalidStateTransition(f"Cannot cancel order in state {self.status}")

        return replace(
            self,
            status=OrderStatus.cancelled(),
        )
