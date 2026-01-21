from collections.abc import Mapping
from dataclasses import dataclass

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
        return sum(
            self.balances.values(),
            start=next(iter(self.balances.values())),
        )
