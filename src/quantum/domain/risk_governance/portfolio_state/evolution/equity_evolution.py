from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.risk_governance.breach_detection.monetary_compatibility import (
    MonetaryCompatibilityService,
)
from quantum.domain.risk_governance.portfolio_state.drawdown import Drawdown
from quantum.domain.risk_governance.portfolio_state.equity import Equity
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.monetary.pnl import RealizedPnL
from quantum.domain.shared_kernel.modeling.services.domain_service import DomainService
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class EquityEvolutionResult(ValueObject):
    new_equity: Equity
    new_equity_peak: Equity
    drawdown: Drawdown

    def _validate_semantics(self) -> None:
        if not isinstance(self.new_equity, Equity):
            raise InvariantViolation("new_equity must be Equity")

        if not isinstance(self.new_equity_peak, Equity):
            raise InvariantViolation("new_equity_peak must be Equity")

        if not isinstance(self.drawdown, Drawdown):
            raise InvariantViolation("drawdown must be Drawdown")

        MonetaryCompatibilityService.assert_same_context_and_currency(
            left=self.new_equity,
            right=self.new_equity_peak,
            left_label="new_equity",
            right_label="new_equity_peak",
        )

        MonetaryCompatibilityService.assert_same_context_and_currency(
            left=self.new_equity,
            right=self.drawdown,
            left_label="new_equity",
            right_label="drawdown",
        )

        if self.new_equity_peak.value < self.new_equity.value:
            raise InvariantViolation("new_equity_peak must be >= new_equity")


class EquityEvolutionService(DomainService):
    __slots__ = ()

    @staticmethod
    def evolve(
        *,
        current_equity: Equity,
        current_peak: Equity,
        pnl: RealizedPnL,
    ) -> EquityEvolutionResult:
        MonetaryCompatibilityService.assert_same_context_and_currency(
            left=current_equity,
            right=current_peak,
            left_label="current_equity",
            right_label="current_peak",
        )

        MonetaryCompatibilityService.assert_same_context_and_currency(
            left=current_equity,
            right=pnl,
            left_label="current_equity",
            right_label="pnl",
        )

        new_equity = current_equity.add(pnl)
        new_peak = max(current_peak, new_equity, key=lambda e: e.value)

        drawdown_value = new_peak.value - new_equity.value

        if drawdown_value < Decimal("0"):
            raise InvariantViolation("Drawdown cannot be negative")

        return EquityEvolutionResult(
            new_equity=new_equity,
            new_equity_peak=new_peak,
            drawdown=Drawdown(
                value=drawdown_value,
                currency=new_equity.currency,
                context=new_equity.context,
            ),
        )
