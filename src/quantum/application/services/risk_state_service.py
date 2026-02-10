from quantum.domain.risk.governance.aggregates.risk_state import RiskState
from quantum.domain.shared_kernel.money.daily_loss import DailyLoss
from quantum.domain.shared_kernel.money.drawdown import Drawdown
from quantum.domain.shared_kernel.money.notional import Notional
from quantum.domain.shared_kernel.money.risk_exposure import RiskExposure
from quantum.domain.shared_kernel.value_objects.pnl import RealizedPnL


class RiskService:

    def process(
        self,
        *,
        aggregate: RiskState,
        pnl: RealizedPnL,
        drawdown: Drawdown,
        daily_loss: DailyLoss,
        exposure: RiskExposure,
        notional: Notional,
    ) -> list:

        return aggregate.register_pnl(
            pnl=pnl,
            drawdown=drawdown,
            daily_loss=daily_loss,
            exposure=exposure,
            notional=notional,
        )
