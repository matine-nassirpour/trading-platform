from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.risk.governance.measures.daily_loss import DailyLoss
from quantum.domain.risk.governance.measures.drawdown import Drawdown
from quantum.domain.risk.governance.measures.exposure import Exposure
from quantum.domain.risk.governance.measures.notional import Notional
from quantum.domain.shared_kernel.monetary.pnl import RealizedPnL


@dataclass(frozen=True, slots=True)
class RegisterPnLCommand(BaseCommand):
    pnl: RealizedPnL
    drawdown: Drawdown
    daily_loss: DailyLoss
    exposure: Exposure
    notional: Notional
