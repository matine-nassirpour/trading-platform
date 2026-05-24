from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.trading.common.events.fact_event import FactEvent
from quantum.domain.trading.execution.reports.execution_rejection import (
    ExecutionRejection,
)
from quantum.domain.trading.identity.broker_order_ref import BrokerOrderRef


@dataclass(frozen=True, slots=True)
class OrderRejectedEvent(FactEvent):
    """
    - Broker rejection
    - Technical rejection
    - Regulatory rejection
    """

    event_name: ClassVar[str] = "trading.order.rejected"
    event_version: ClassVar[int] = 1

    broker_order_ref: BrokerOrderRef

    decision_id: DecisionId
    symbol: Symbol

    rejection: ExecutionRejection
