from dataclasses import dataclass

from quantum.domain.risk.core.drawdown import Drawdown
from quantum.domain.risk.core.notional import Notional
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs
from quantum.domain.shared_kernel.value_objects.realized_pnl import RealizedPnL


@dataclass(frozen=True)
class EvaluateRiskCommand:
    current_drawdown: Drawdown
    notional: Notional
    daily_loss: RealizedPnL
    at: EpochMs
