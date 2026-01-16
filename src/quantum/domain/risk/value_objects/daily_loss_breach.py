from dataclasses import dataclass

from quantum.domain.risk.value_objects.daily_loss import DailyLoss
from quantum.domain.risk.value_objects.daily_loss_limit import DailyLossLimit
from quantum.domain.risk.value_objects.risk_breach import RiskBreach
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class DailyLossBreach(RiskBreach):
    """
    Risk breach for daily realized loss limit violation.

    Invariants:
    - kind == daily_loss
    - current is DailyLoss
    - limit is DailyLossLimit
    - MoneyContext(current) == MoneyContext(limit)
    """

    current: DailyLoss
    limit: DailyLossLimit

    def _validate(self) -> None:
        # 1. Shared RiskBreach invariants
        super()._validate()

        # 2. Type safety
        if not isinstance(self.current, DailyLoss):
            raise InvariantViolation("DailyLossBreach.current must be a DailyLoss")

        if not isinstance(self.limit, DailyLossLimit):
            raise InvariantViolation("DailyLossBreach.limit must be a DailyLossLimit")

        # 3. Context consistency
        if self.current.context != self.limit.context:
            raise InvariantViolation("DailyLoss MoneyContext mismatch")
