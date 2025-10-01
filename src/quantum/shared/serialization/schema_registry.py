from pydantic import BaseModel

from quantum.domain.events.trading.v1.breakeven_trigger_v1 import BreakevenTriggerV1
from quantum.domain.events.trading.v1.killswitch_trigger_v1 import KillSwitchTriggerV1
from quantum.domain.events.trading.v1.latency_probe_v1 import LatencyProbeV1
from quantum.domain.events.trading.v1.market_data_gap_v1 import MarketDataGapV1
from quantum.domain.events.trading.v1.mt5_health_v1 import Mt5HealthV1
from quantum.domain.events.trading.v1.order_ack_v1 import OrderAckV1
from quantum.domain.events.trading.v1.order_check_v1 import OrderCheckV1
from quantum.domain.events.trading.v1.order_fill_v1 import OrderFillV1
from quantum.domain.events.trading.v1.order_intent_v1 import OrderIntentV1
from quantum.domain.events.trading.v1.order_reject_v1 import OrderRejectV1
from quantum.domain.events.trading.v1.order_submit_v1 import OrderSubmitV1
from quantum.domain.events.trading.v1.position_update_v1 import PositionUpdateV1
from quantum.domain.events.trading.v1.reconciliation_v1 import ReconciliationV1
from quantum.domain.events.trading.v1.sl_tp_update_v1 import SlTpUpdateV1
from quantum.domain.events.trading.v1.trailing_trigger_v1 import TrailingTriggerV1

REGISTRY: dict[str, type[BaseModel]] = {
    "breakeven_trigger_v1": BreakevenTriggerV1,
    "killswitch_trigger_v1": KillSwitchTriggerV1,
    "latency_probe_v1": LatencyProbeV1,
    "market_data_gap_v1": MarketDataGapV1,
    "mt5_health_v1": Mt5HealthV1,
    "order_ack_v1": OrderAckV1,
    "order_check_v1": OrderCheckV1,
    "order_fill_v1": OrderFillV1,
    "order_intent_v1": OrderIntentV1,
    "order_reject_v1": OrderRejectV1,
    "order_submit_v1": OrderSubmitV1,
    "position_update_v1": PositionUpdateV1,
    "reconciliation_v1": ReconciliationV1,
    "sl_tp_update_v1": SlTpUpdateV1,
    "trailing_trigger_v1": TrailingTriggerV1,
}
