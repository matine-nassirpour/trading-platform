from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.market.instrument.pricing.reference_price import ReferencePrice
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.monetary.price import Price
from quantum.domain.trading.common.events.fact_event import FactEvent
from quantum.domain.trading.execution.order.order_kind import OrderKind
from quantum.domain.trading.execution.order.time_in_force import TimeInForce
from quantum.domain.trading.execution.position_side import PositionSide
from quantum.domain.trading.identity.broker_order_ref import BrokerOrderRef
from quantum.domain.trading.value_objects.volume import PositiveVolume


@dataclass(frozen=True, slots=True)
class OrderCreatedEvent(FactEvent):
    """
    Emitted when an order is created inside a TradingIntent.

    Audit meaning:
    - The system decided to expose capital
    - With a specific side and order type
    """

    event_name: ClassVar[str] = "trading.order.created"
    event_version: ClassVar[int] = 1

    intent_id: DecisionId
    broker_order_ref: BrokerOrderRef
    symbol: Symbol

    order_kind: OrderKind
    side: PositionSide
    volume: PositiveVolume

    time_in_force: TimeInForce

    reference_price: ReferencePrice | None = (
        None  # Non-executable price observed at decision time (audit / validation anchor)
    )
    stop_price: Price | None = (
        None  # Executable trigger price for STOP or STOP-LIMIT orders
    )
    limit_price: Price | None = (
        None  # Executable price constraint for LIMIT or STOP-LIMIT orders
    )

    sl: Price | None = None
    tp: Price | None = None

    def _validate_payload(self) -> None:
        if self.order_kind.requires_limit_price() and self.limit_price is None:
            raise InvariantViolation("limit_price is required for this order type")

        if self.order_kind.forbids_limit_price() and self.limit_price is not None:
            raise InvariantViolation("limit_price is forbidden for this order type")

        if self.order_kind.requires_stop_price() and self.stop_price is None:
            raise InvariantViolation("stop_price is required for this order type")

        if self.order_kind.forbids_stop_price() and self.stop_price is not None:
            raise InvariantViolation("stop_price is forbidden for this order type")

        if self.order_kind.requires_price_reference() and self.reference_price is None:
            raise InvariantViolation("reference_price is required for this order type")
