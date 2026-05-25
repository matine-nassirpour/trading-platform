from quantum.domain.risk.governance.limits.risk_limits import RiskLimits
from quantum.domain.risk.governance.measures.daily_loss import DailyLoss
from quantum.domain.risk.governance.measures.equity import Equity
from quantum.domain.risk.governance.measures.exposure import Exposure
from quantum.domain.risk.governance.measures.notional import Notional
from quantum.domain.shared_kernel.foundation.errors.invariants import (
    CurrencyMismatch,
    InvariantViolation,
)
from quantum.domain.shared_kernel.modeling.monetary.pnl import RealizedPnL
from quantum.domain.shared_kernel.modeling.services.domain_service import DomainService


class RiskInputValidator(DomainService):
    __slots__ = ()

    @staticmethod
    def validate_register_pnl_inputs(
        *,
        limits: RiskLimits,
        equity: Equity,
        pnl: RealizedPnL,
        daily_loss: DailyLoss,
        exposure: Exposure,
        notional: Notional,
    ) -> None:
        for value, name in (
            (pnl, "PnL"),
            (daily_loss, "DailyLoss"),
            (exposure, "Exposure"),
            (notional, "Notional"),
            (equity, "Equity"),
        ):
            if value.context != limits.context:
                raise InvariantViolation(f"{name} MoneyContext mismatch")

        expected_currency = equity.currency

        if pnl.currency != expected_currency:
            raise CurrencyMismatch("PnL currency mismatch")

        if daily_loss.currency != expected_currency:
            raise CurrencyMismatch("DailyLoss currency mismatch")

        if exposure.currency != expected_currency:
            raise CurrencyMismatch("Exposure currency mismatch")

        if notional.currency != expected_currency:
            raise CurrencyMismatch("Notional currency mismatch")
