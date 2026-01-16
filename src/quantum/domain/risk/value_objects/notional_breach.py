from dataclasses import dataclass

from quantum.domain.risk.value_objects.notional import Notional
from quantum.domain.risk.value_objects.risk_breach import RiskBreach
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class NotionalBreach(RiskBreach):
    """
    Risk breach for notional exposure limit violation.

    Invariants:
    - kind == notional
    - current is Notional
    - limit is Notional
    - MoneyContext(current) == MoneyContext(limit)
    """

    current: Notional
    limit: Notional

    def _validate(self) -> None:
        # 1. Shared RiskBreach invariants
        super()._validate()

        # 2. Type safety
        if not isinstance(self.current, Notional):
            raise InvariantViolation("NotionalBreach.current must be a Notional")

        if not isinstance(self.limit, Notional):
            raise InvariantViolation("NotionalBreach.limit must be a Notional")

        # 3. Context consistency
        if self.current.context != self.limit.context:
            raise InvariantViolation("Notional MoneyContext mismatch")
