from dataclasses import dataclass

from quantum.domain.risk.value_objects.drawdown import Drawdown
from quantum.domain.risk.value_objects.notional import Notional
from quantum.domain.shared.value_objects.epoch_ms import EpochMs
from quantum.domain.shared.value_objects.realized_pnl import RealizedPnL


@dataclass(frozen=True)
class EvaluateRiskCommand:
    current_drawdown: Drawdown
    notional: Notional
    daily_loss: RealizedPnL
    at: EpochMs
