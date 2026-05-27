from decimal import Decimal

from quantum.domain.risk_governance.measures.daily_loss import DailyLoss
from quantum.domain.shared_kernel.foundation.errors.invariants import (
    CurrencyMismatch,
    InvariantViolation,
)
from quantum.domain.shared_kernel.modeling.monetary.pnl import RealizedPnL
from quantum.domain.shared_kernel.modeling.services.domain_service import DomainService


class DailyLossEvolutionService(DomainService):
    __slots__ = ()

    @staticmethod
    def evolve(
        *,
        current_daily_loss: DailyLoss,
        pnl: RealizedPnL,
    ) -> DailyLoss:
        if pnl.context != current_daily_loss.context:
            raise InvariantViolation("PnL MoneyContext mismatch")

        if pnl.currency != current_daily_loss.currency:
            raise CurrencyMismatch("PnL currency mismatch")

        if pnl.value >= Decimal("0"):
            return current_daily_loss

        return DailyLoss(
            value=current_daily_loss.value + abs(pnl.value),
            currency=current_daily_loss.currency,
            context=current_daily_loss.context,
        )
