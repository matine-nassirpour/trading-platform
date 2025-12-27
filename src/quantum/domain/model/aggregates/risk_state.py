from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.model.exceptions import InvariantViolation, RiskViolation
from quantum.domain.model.value_objects.drawdown_limit import DrawdownLimit
from quantum.domain.model.value_objects.money import Money


@dataclass
class RiskState:
    """
    Aggregate Root.
    Encapsulates drawdown-based risk invariants.

    Definitions:
    - Drawdown is represented as a NEGATIVE Money value.
    - max_drawdown is a POSITIVE Money threshold.
    """

    max_drawdown: DrawdownLimit
    current_drawdown: Money
    kill_switch: bool = False

    def __post_init__(self) -> None:
        if self.current_drawdown.value > Decimal("0"):
            raise InvariantViolation("Current drawdown must be ≤ 0")

        if self.current_drawdown.currency != self.max_drawdown.value.currency:
            raise InvariantViolation("Currency mismatch in risk state")

    def register_pnl(self, pnl: Money) -> None:
        if pnl.currency != self.current_drawdown.currency:
            raise InvariantViolation("PnL currency mismatch")

        # Only losses increase drawdown
        if pnl.value < Decimal("0"):
            self.current_drawdown = Money(
                self.current_drawdown.value + pnl.value,
                self.current_drawdown.currency,
            )

        if abs(self.current_drawdown.value) >= self.max_drawdown.value.value:
            self.kill_switch = True
            raise RiskViolation("Maximum drawdown exceeded")

    @property
    def drawdown_ratio(self) -> Decimal:
        """
        For monitoring / analytics only.
        Returns a value in [0, 1+] range.
        """
        return abs(self.current_drawdown.value) / self.max_drawdown.value.value
