from dataclasses import dataclass

from quantum.domain.risk.value_objects.drawdown import Drawdown
from quantum.domain.risk.value_objects.drawdown_limit import DrawdownLimit
from quantum.domain.risk.value_objects.risk_breach import RiskBreach
from quantum.domain.risk.value_objects.risk_breach_kind import RiskBreachKind
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation


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
        # 1. Shared RiskBreach invariants
        super()._validate()

        # 2. Nominal kind invariant
        if self.kind != RiskBreachKind.drawdown():
            raise InvariantViolation("DrawdownBreach requires kind=drawdown")

        # 3. Type safety (defensive, explicit)
        if not isinstance(self.current, Drawdown):
            raise InvariantViolation("DrawdownBreach.current must be a Drawdown")

        if not isinstance(self.limit, DrawdownLimit):
            raise InvariantViolation("DrawdownBreach.limit must be a DrawdownLimit")

        # 4. Context consistency
        if self.current.context != self.limit.context:
            raise InvariantViolation("Drawdown MoneyContext mismatch")
