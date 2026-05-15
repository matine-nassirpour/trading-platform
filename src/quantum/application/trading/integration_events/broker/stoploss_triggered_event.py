from dataclasses import dataclass
from typing import ClassVar

from quantum.application.trading.integration_events.base.integration_event import (
    IntegrationEvent,
)
from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.monetary.price import Price
from quantum.domain.trading.execution.order.broker_deal_ref import BrokerDealRef
from quantum.domain.trading.execution.taxonomy.deal_entry import DealEntry
from quantum.domain.trading.execution.taxonomy.deal_reason import DealReason
from quantum.domain.trading.identifiers.broker_order_ref import BrokerOrderRef
from quantum.domain.trading.identifiers.broker_position_ref import BrokerPositionRef
from quantum.domain.trading.value_objects.volume import PositiveVolume


@dataclass(frozen=True, slots=True)
class StopLossTriggeredEvent(IntegrationEvent):
    """
    - triggered by the broker
    - related to execution
    - not business decisions
    """

    event_name: ClassVar[str] = "broker.stoploss.triggered"
    event_version: ClassVar[int] = 1

    intent_id: DecisionId
    broker_order_ref: BrokerOrderRef
    broker_deal_ref: BrokerDealRef
    broker_position_ref: BrokerPositionRef
    symbol: Symbol

    trigger_price: Price
    sl_price: Price
    volume_closed: PositiveVolume

    deal_entry: DealEntry
    reason: DealReason
