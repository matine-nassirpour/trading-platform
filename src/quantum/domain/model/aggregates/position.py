from __future__ import annotations

from dataclasses import dataclass, replace

from quantum.domain.model.aggregates.base import AggregateRoot
from quantum.domain.model.exceptions.position_exceptions import PositionAlreadyClosed
from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.currency import Currency
from quantum.domain.model.value_objects.identifiers import PositionId
from quantum.domain.model.value_objects.money import Money
from quantum.domain.model.value_objects.price import Price
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.volume import PositiveVolume
from quantum.domain.services.pnl_service import PnLService
from quantum.domain.types.position_side import PositionSide


@dataclass(frozen=True, eq=False)
class Position(AggregateRoot):
    """
    Aggregate Root representing a trading position.

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
        if self.realized_pnl.currency is None:
            raise InvariantViolation("Position must have a currency")

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def open(
        position_id: PositionId,
        symbol: Symbol,
        side: PositionSide,
        volume: PositiveVolume,
        entry_price: Price,
        currency: Currency,
    ) -> Position:
        return Position(
            position_id=position_id,
            symbol=symbol,
            side=side,
            volume=volume,
            entry_price=entry_price,
            realized_pnl=Money(value=entry_price.value * 0, currency=currency),
            closed=False,
        )

    # --- Commands -------------------------------------------------------------

    def close(self, exit_price: Price) -> Position:
        if self.closed:
            raise PositionAlreadyClosed("Position already closed")

        pnl = PnLService.compute_realized_pnl(
            entry_price=self.entry_price,
            exit_price=exit_price,
            volume=self.volume,
            side=self.side,
            currency=self.realized_pnl.currency,
        )

        return replace(self, realized_pnl=pnl, closed=True)
