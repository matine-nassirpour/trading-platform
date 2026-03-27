from dataclasses import dataclass
from typing import ClassVar

from quantum.application.trading.integration_events.base.integration_event import (
    IntegrationEvent,
)
from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.trading.execution.taxonomy.order_check_outcome import (
    OrderCheckOutcome,
)


@dataclass(frozen=True, slots=True)
class OrderCheckedEvent(IntegrationEvent):
    """
    - margin check
    - market open
    - lot size ok
    """

    event_name: ClassVar[str] = "broker.order.checked"
    event_version: ClassVar[int] = 1

    intent_id: DecisionId
    symbol: Symbol

    outcome: OrderCheckOutcome
