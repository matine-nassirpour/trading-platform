from pydantic import BaseModel

from quantum.domain.events.trading.v1.breakeven_trigger_event import (
    BreakevenTriggerEvent,
)
from quantum.domain.events.trading.v1.killswitch_trigger_event import (
    KillSwitchTriggerEvent,
)
from quantum.domain.events.trading.v1.latency_probe_event import LatencyProbeEvent
from quantum.domain.events.trading.v1.market_data_gap_event import MarketDataGapEvent
from quantum.domain.events.trading.v1.mt5_health_event import Mt5HealthEvent
from quantum.domain.events.trading.v1.order_ack_event import OrderAckEvent
from quantum.domain.events.trading.v1.order_check_event import OrderCheckEvent
from quantum.domain.events.trading.v1.order_fill_event import OrderFillEvent
from quantum.domain.events.trading.v1.order_intent_event import OrderIntentEvent
from quantum.domain.events.trading.v1.order_reject_event import OrderRejectEvent
from quantum.domain.events.trading.v1.order_submit_event import OrderSubmitEvent
from quantum.domain.events.trading.v1.position_update_event import PositionUpdateEvent
from quantum.domain.events.trading.v1.reconciliation_event import ReconciliationEvent
from quantum.domain.events.trading.v1.sl_tp_update_event import SlTpUpdateEvent
from quantum.domain.events.trading.v1.trailing_trigger_event import TrailingTriggerEvent

REGISTRY: dict[str, type[BaseModel]] = {
    "breakeven_trigger_v1": BreakevenTriggerEvent,
    "killswitch_trigger_v1": KillSwitchTriggerEvent,
    "latency_probe_v1": LatencyProbeEvent,
    "market_data_gap_v1": MarketDataGapEvent,
    "mt5_health_v1": Mt5HealthEvent,
    "order_ack_v1": OrderAckEvent,
    "order_check_v1": OrderCheckEvent,
    "order_fill_v1": OrderFillEvent,
    "order_intent_v1": OrderIntentEvent,
    "order_reject_v1": OrderRejectEvent,
    "order_submit_v1": OrderSubmitEvent,
    "position_update_v1": PositionUpdateEvent,
    "reconciliation_v1": ReconciliationEvent,
    "sl_tp_update_v1": SlTpUpdateEvent,
    "trailing_trigger_v1": TrailingTriggerEvent,
}
