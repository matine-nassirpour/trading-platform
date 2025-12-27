from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.model.exceptions import RiskViolation
from quantum.domain.model.value_objects.money import Money


@dataclass
class RiskState:
    """
    Aggregate Root.
    Encapsulates drawdown invariant.
    """

    max_drawdown: Decimal
    current_drawdown: Decimal = Decimal("0")
    kill_switch: bool = False

    def register_pnl(self, pnl: Money) -> None:
        if pnl.value < 0:
            self.current_drawdown += pnl.value

        if abs(self.current_drawdown) >= self.max_drawdown:
            self.kill_switch = True
            raise RiskViolation("Max drawdown exceeded")
