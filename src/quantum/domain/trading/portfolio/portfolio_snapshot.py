from collections.abc import Mapping
from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.trading.portfolio.balance import Balance
from quantum.domain.trading.portfolio.exposure import Exposure
from quantum.domain.trading.portfolio.margin import Margin


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    """
    Immutable snapshot of portfolio state at a point in time.
    """

    balances: Mapping[str, Balance]
    exposures: Mapping[str, Exposure]
    margin: Margin

    def total_equity(self) -> Balance:
        if not self.balances:
            raise InvariantViolation("Cannot compute equity of empty portfolio")

        values = list(self.balances.values())
        first = values[0]

        for b in values[1:]:
            first = first.add(b)

        return first
