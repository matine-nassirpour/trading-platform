from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.shared_kernel.money.daily_loss import DailyLoss
from quantum.domain.shared_kernel.money.drawdown import Drawdown
from quantum.domain.shared_kernel.money.notional import Notional
from quantum.domain.shared_kernel.money.risk_exposure import RiskExposure
from quantum.domain.shared_kernel.value_objects.pnl import RealizedPnL


@dataclass(frozen=True, slots=True)
class RegisterPnLCommand(BaseCommand):
    pnl: RealizedPnL
    drawdown: Drawdown
    daily_loss: DailyLoss
    exposure: RiskExposure
    notional: Notional
