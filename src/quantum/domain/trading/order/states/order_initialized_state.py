from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.market.instrument.pricing.reference_price import ReferencePrice
from quantum.domain.shared_kernel.event_sourcing.events.event_sequence import (
    EventSequence,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.monetary.price import Price
from quantum.domain.trading.common.value_objects.position_side import PositionSide
from quantum.domain.trading.common.value_objects.volume import (
    NonNegativeVolume,
    PositiveVolume,
)
from quantum.domain.trading.identity.broker_order_ref import BrokerOrderRef
from quantum.domain.trading.order.order_kind import OrderKind
from quantum.domain.trading.order.states.order_state_base import OrderStateBase
from quantum.domain.trading.order.status.order_fill_status import OrderFillStatus
from quantum.domain.trading.order.status.order_lifecycle_status import (
    OrderLifecycleStatus,
)
from quantum.domain.trading.order.time_in_force import TimeInForce


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

    lifecycle_status: OrderLifecycleStatus
    fill_status: OrderFillStatus

    decision_id: DecisionId

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
            ("lifecycle_status", self.lifecycle_status, OrderLifecycleStatus),
            ("fill_status", self.fill_status, OrderFillStatus),
            ("decision_id", self.decision_id, DecisionId),
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

    def _assert_fill_status_matches_volume(self) -> None:
        if self.filled_volume.value == 0:
            if not self.fill_status.is_unfilled():
                raise InvariantViolation("Zero filled volume requires unfilled status")
            return

        if self.filled_volume.value < self.requested_volume.value:
            if not self.fill_status.is_partially_filled():
                raise InvariantViolation(
                    "Partial filled volume requires partially_filled status"
                )
            return

        if self.filled_volume.value == self.requested_volume.value:
            if not self.fill_status.is_filled():
                raise InvariantViolation("Fully filled volume requires filled status")
            return

        raise InvariantViolation("Overfill")

    def _assert_terminal_lifecycle_consistency(self) -> None:
        if self.fill_status.is_filled() and self.lifecycle_status.value in {
            "rejected",
            "cancelled",
            "expired",
        }:
            raise InvariantViolation(
                "Fully filled order cannot have rejected/cancelled/expired lifecycle"
            )

    def _assert_completed_status_consistency(self) -> None:
        if self.fill_status.is_filled():
            if self.lifecycle_status != OrderLifecycleStatus.completed():
                raise InvariantViolation(
                    "Fully filled order must have completed lifecycle status"
                )

        if self.lifecycle_status == OrderLifecycleStatus.completed():
            if not self.fill_status.is_filled():
                raise InvariantViolation("Completed lifecycle requires filled status")

    def _validate_semantics(self) -> None:
        super()._validate_semantics()
        self._validate_types()

        if self.last_sequence.is_initial():
            raise InvariantViolation("Initialized order cannot be initial")

        if self.filled_volume.value > self.requested_volume.value:
            raise InvariantViolation("Overfill")

        self._assert_fill_status_matches_volume()
        self._assert_terminal_lifecycle_consistency()
        self._assert_completed_status_consistency()

    def rebuild(
        self,
        *,
        last_sequence: EventSequence,
        lifecycle_status: OrderLifecycleStatus | None = None,
        fill_status: OrderFillStatus | None = None,
        filled_volume: NonNegativeVolume | None = None,
    ) -> OrderInitializedState:
        return OrderInitializedState(
            last_sequence=last_sequence,
            decision_id=self.decision_id,
            broker_order_ref=self.broker_order_ref,
            symbol=self.symbol,
            order_kind=self.order_kind,
            side=self.side,
            requested_volume=self.requested_volume,
            filled_volume=(
                self.filled_volume if filled_volume is None else filled_volume
            ),
            lifecycle_status=(
                self.lifecycle_status if lifecycle_status is None else lifecycle_status
            ),
            fill_status=self.fill_status if fill_status is None else fill_status,
            reference_price=self.reference_price,
            stop_price=self.stop_price,
            limit_price=self.limit_price,
            sl=self.sl,
            tp=self.tp,
            time_in_force=self.time_in_force,
        )

    def with_lifecycle_status(
        self,
        *,
        lifecycle_status: OrderLifecycleStatus,
        last_sequence: EventSequence,
    ) -> OrderInitializedState:
        return self.rebuild(
            last_sequence=last_sequence,
            lifecycle_status=lifecycle_status,
        )

    def with_registered_fill(
        self,
        *,
        filled_volume: NonNegativeVolume,
        fill_status: OrderFillStatus,
        lifecycle_status: OrderLifecycleStatus,
        last_sequence: EventSequence,
    ) -> OrderInitializedState:
        return self.rebuild(
            last_sequence=last_sequence,
            filled_volume=filled_volume,
            fill_status=fill_status,
            lifecycle_status=lifecycle_status,
        )
