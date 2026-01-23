from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.primitives.aggregate_state import AggregateState
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventHandler,
    EventSourcedAggregateRoot,
)
from quantum.domain.trading.events.v1.portfolio.balance_updated_event import (
    BalanceUpdatedEvent,
)
from quantum.domain.trading.events.v1.portfolio.exposure_updated_event import (
    ExposureUpdatedEvent,
)
from quantum.domain.trading.events.v1.portfolio.portfolio_created_event import (
    PortfolioCreatedEvent,
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

    @staticmethod
    def create(
        *,
        account: Account,
        initial_margin: Margin,
    ) -> list[BaseEvent]:

        return [
            PortfolioCreatedEvent(
                account_id=account.account_id,
                context=initial_margin.context,
            )
        ]

    # --- Event → State transitions --------------------------------------------

    @staticmethod
    def _apply_created(
        state: PortfolioState,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> PortfolioState:

        assert isinstance(event, PortfolioCreatedEvent)

        return PortfolioState(
            last_sequence=envelope.sequence,
            account=state.account,
            balances={},
            exposures={},
            margin=state.margin,
        )

    @staticmethod
    def _apply_balance_updated(
        state: PortfolioState,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> PortfolioState:

        assert isinstance(event, BalanceUpdatedEvent)

        return PortfolioState(
            last_sequence=envelope.sequence,
            account=state.account,
            balances=state.balances,
            exposures=state.exposures,
            margin=state.margin,
        )

    @staticmethod
    def _apply_exposure_updated(
        state: PortfolioState,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> PortfolioState:

        assert isinstance(event, ExposureUpdatedEvent)

        exposures = dict(state.exposures)
        exposures[event.symbol.value] = Exposure(
            symbol=event.symbol,
            notional=event.notional,
            leverage=event.notional.value,
        )

        return PortfolioState(
            last_sequence=envelope.sequence,
            account=state.account,
            balances=state.balances,
            exposures=exposures,
            margin=state.margin,
        )

    @classmethod
    def _handlers(
        cls,
    ) -> Mapping[type[BaseEvent], EventHandler[PortfolioState, BaseEvent]]:
        return {
            PortfolioCreatedEvent: cls._apply_created,
            BalanceUpdatedEvent: cls._apply_balance_updated,
            ExposureUpdatedEvent: cls._apply_exposure_updated,
        }

    # --- Read model -----------------------------------------------------------

    def snapshot(self) -> PortfolioSnapshot:
        return PortfolioSnapshot(
            balances=self.state.balances,
            exposures=self.state.exposures,
            margin=self.state.margin,
        )
