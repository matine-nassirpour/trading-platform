from dataclasses import dataclass

from quantum.domain.model.exceptions import RiskViolation
from quantum.domain.model.value_objects.drawdown_limit import DrawdownLimit
from quantum.domain.model.value_objects.money import Money


@dataclass(frozen=True)
class DrawdownPolicy:
    """
    Pure domain policy.
    Stateless.
    """

    max_drawdown: DrawdownLimit

    def evaluate(self, current_drawdown: Money) -> None:
        if abs(current_drawdown.value) >= self.max_drawdown.value.value:
            raise RiskViolation("Maximum drawdown exceeded")
