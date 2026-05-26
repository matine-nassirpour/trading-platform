from quantum.domain.risk_governance.limits.risk_limits import RiskLimits
from quantum.domain.risk_governance.measures.daily_loss import DailyLoss
from quantum.domain.risk_governance.measures.equity import Equity
from quantum.domain.risk_governance.measures.exposure import Exposure
from quantum.domain.risk_governance.measures.notional import Notional
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
        expected_context = limits.context
        expected_currency = limits.context.reporting_currency

        for value, name in (
            (equity, "Equity"),
            (pnl, "PnL"),
            (daily_loss, "DailyLoss"),
            (exposure, "Exposure"),
            (notional, "Notional"),
        ):
            if value.context != expected_context:
                raise InvariantViolation(f"{name} MoneyContext mismatch")

            if value.currency != expected_currency:
                raise CurrencyMismatch(
                    f"{name} currency must equal "
                    "RiskLimits.context.reporting_currency"
                )
