from dataclasses import dataclass

from quantum.domain.model.exceptions.risk_exceptions import DrawdownLimitExceeded
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
            raise DrawdownLimitExceeded("Maximum drawdown exceeded")
