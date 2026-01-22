from collections.abc import Mapping
from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.primitives.aggregate_state import AggregateState
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventSourcedAggregateRoot,
)
from quantum.domain.trading.portfolio.account import Account
from quantum.domain.trading.portfolio.balance import Balance
from quantum.domain.trading.portfolio.exposure import Exposure
from quantum.domain.trading.portfolio.margin import Margin
from quantum.domain.trading.portfolio.portfolio_snapshot import PortfolioSnapshot


@dataclass(frozen=True, slots=True)
class PortfolioState(AggregateState):
    last_sequence: EventSequence

    account: Account
    balances: Mapping[str, Balance]
    exposures: Mapping[str, Exposure]
    margin: Margin

    def last_event_sequence(self) -> EventSequence:
        return self.last_sequence

    def _validate(self) -> None:
        if not isinstance(self.account, Account):
            raise InvariantViolation("Portfolio requires Account")

        if not self.balances:
            raise InvariantViolation("Portfolio must have balances")

        for b in self.balances.values():
            if not isinstance(b, Balance):
                raise InvariantViolation("Invalid Balance")

        for e in self.exposures.values():
            if not isinstance(e, Exposure):
                raise InvariantViolation("Invalid Exposure")

        if not isinstance(self.margin, Margin):
            raise InvariantViolation("Invalid Margin")


class Portfolio(EventSourcedAggregateRoot[PortfolioState]):
    """
    Aggregate root for portfolio state.
    """

    def snapshot(self) -> PortfolioSnapshot:
        return PortfolioSnapshot(
            balances=self.state.balances,
            exposures=self.state.exposures,
            margin=self.state.margin,
        )
