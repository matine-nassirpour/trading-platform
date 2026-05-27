from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.risk_governance.portfolio_state.daily_loss import DailyLoss
from quantum.domain.risk_governance.portfolio_state.drawdown import Drawdown
from quantum.domain.risk_governance.portfolio_state.exposure import Exposure
from quantum.domain.risk_governance.portfolio_state.notional import Notional
from quantum.domain.shared_kernel.modeling.monetary.pnl import RealizedPnL


@dataclass(frozen=True, slots=True)
class RegisterPnLCommand(BaseCommand):
    pnl: RealizedPnL
    drawdown: Drawdown
    daily_loss: DailyLoss
    exposure: Exposure
    notional: Notional
