from dataclasses import dataclass

from quantum.domain.shared.value_objects.epoch_ms import EpochMs
from quantum.domain.shared.value_objects.money import Money


@dataclass(frozen=True)
class EvaluateRiskCommand:
    current_drawdown: Money
    notional: Money
    daily_loss: Money
    at: EpochMs
