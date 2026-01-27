from dataclasses import dataclass

from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.trading.execution.order.position_side import PositionSide


@dataclass(frozen=True)
class SubmitTradingIntentCommand:
    intent_id: IntentId
    symbol: Symbol
    side: PositionSide
    decision_epoch_ms: EpochMs
    client_order_id: str
