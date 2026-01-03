from __future__ import annotations

from dataclasses import dataclass, replace

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.errors.position_errors import PositionAlreadyClosed
from quantum.domain.shared.primitives.aggregate_root import AggregateRoot
from quantum.domain.shared.value_objects.currency import Currency
from quantum.domain.shared.value_objects.money import Money
from quantum.domain.shared.value_objects.price import Price
from quantum.domain.shared.value_objects.symbol import Symbol
from quantum.domain.shared.value_objects.volume import PositiveVolume
from quantum.domain.trading.position.pnl_service import PnLService
from quantum.domain.trading.value_objects.identifiers.position_id import PositionId
from quantum.domain.trading.value_objects.order.position_side import PositionSide


@dataclass(frozen=True, eq=False)
class Position(AggregateRoot):
    """
    Aggregate Root representing a trading position.

    Domain semantics:
    - A Position is opened exactly once
    - A Position is closed at most once
    - Realized PnL is final once closed
    - Currency consistency is enforced at aggregate level

    Identity:
    - PositionId
    """

    position_id: PositionId
    symbol: Symbol
    side: PositionSide
    volume: PositiveVolume
    entry_price: Price
    realized_pnl: Money
    closed: bool = False

    # --- Identity semantics ---------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Position):
            return False
        return self.position_id == other.position_id

    def __hash__(self) -> int:
        return hash(self.position_id)

    # --- Invariants -----------------------------------------------------------

    def _validate(self) -> None:
        # Money already guarantees currency correctness and finiteness,
        # but the aggregate guarantees semantic consistency.

        if not isinstance(self.realized_pnl, Money):
            raise InvariantViolation("Position must have a valid Money PnL")

        if self.closed:
            # When closed, realized_pnl is final and meaningful.
            # No further invariant is required here, but the state is explicit.
            pass

        if not self.closed:
            # When open, realized_pnl must be the canonical zero.
            if self.realized_pnl.value != 0:
                raise InvariantViolation("Open Position must have zero realized PnL")

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def open(
        *,
        position_id: PositionId,
        symbol: Symbol,
        side: PositionSide,
        volume: PositiveVolume,
        entry_price: Price,
        currency: Currency,
    ) -> Position:
        """
        Canonical factory for opening a Position.

        Guarantees:
        - realized_pnl starts at zero
        - currency is explicitly bound
        """
        return Position(
            position_id=position_id,
            symbol=symbol,
            side=side,
            volume=volume,
            entry_price=entry_price,
            realized_pnl=Money.zero(currency),
            closed=False,
        )

    # --- Commands -------------------------------------------------------------

    def close(self, *, exit_price: Price) -> Position:
        """
        Closes the position and computes realized PnL.

        Rules:
        - A position can only be closed once
        - PnL computation is deterministic and side-aware
        """
        if self.closed:
            raise PositionAlreadyClosed("Position already closed")

        pnl = PnLService.compute_realized_pnl(
            entry_price=self.entry_price,
            exit_price=exit_price,
            volume=self.volume,
            side=self.side,
            currency=self.realized_pnl.currency,
        )

        return replace(
            self,
            realized_pnl=pnl,
            closed=True,
        )
