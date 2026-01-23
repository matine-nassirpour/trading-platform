from dataclasses import dataclass

from quantum.domain.risk.breaches.risk_breach import RiskBreach
from quantum.domain.risk.limits.drawdown_limit import DrawdownLimit
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.drawdown import Drawdown


@dataclass(frozen=True, slots=True)
class DrawdownBreach(RiskBreach):
    """
    Risk breach for drawdown limit violation.

    Invariants:
    - kind == drawdown
    - current is Drawdown
    - limit is DrawdownLimit
    - MoneyContext(current) == MoneyContext(limit)
    """

    current: Drawdown
    limit: DrawdownLimit

    def _validate(self) -> None:
        super()._validate()

        if not isinstance(self.current, Drawdown):
            raise InvariantViolation("DrawdownBreach.current must be a Drawdown")

        if not isinstance(self.limit, DrawdownLimit):
            raise InvariantViolation("DrawdownBreach.limit must be a DrawdownLimit")

        if self.current.context != self.limit.context:
            raise InvariantViolation("Drawdown MoneyContext mismatch")
