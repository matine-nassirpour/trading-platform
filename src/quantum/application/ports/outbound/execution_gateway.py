from __future__ import annotations

from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.value_objects.price import Price
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.execution.order.order_type import OrderType
from quantum.domain.trading.execution.order.time_in_force import TimeInForce
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId
from quantum.domain.trading.value_objects.identifiers.order_id import OrderId


@runtime_checkable
class ExecutionGateway(Protocol):
    """
    Outbound port to the execution subsystem (EA / broker bridge).

    This port sends "intentions d'ordre" (application-level command to infra).
    No transport details here (no HTTP, no MT5, no FIX).
    """

    def submit_order(
        self,
        *,
        intent_id: IntentId,
        order_id: OrderId,
        symbol: Symbol,
        order_type: OrderType,
        volume: PositiveVolume,
        time_in_force: TimeInForce,
        reference_price: Price | None = None,
        limit_price: Price | None = None,
        stop_price: Price | None = None,
        sl: Price | None = None,
        tp: Price | None = None,
        client_order_id: str | None = None,
    ) -> None:
        raise NotImplementedError

    def cancel_order(
        self,
        *,
        intent_id: IntentId,
        order_id: OrderId,
        symbol: Symbol,
    ) -> None:
        raise NotImplementedError
