from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal

from quantum.domain.model.aggregates.base import AggregateRoot
from quantum.domain.model.exceptions.position_exceptions import PositionAlreadyClosed
from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.identifiers import PositionId
from quantum.domain.model.value_objects.money import Money
from quantum.domain.model.value_objects.price import Price
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.volume import PositiveVolume
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
        if self.volume.value <= Decimal("0"):
            raise InvariantViolation("Position volume must be strictly positive")

        if self.entry_price.value <= Decimal("0"):
            raise InvariantViolation("Entry price must be strictly positive")

        if self.realized_pnl.currency is None:
            raise InvariantViolation("PnL currency must be defined")

    # Factory ------------------------------------------------------------------

    @staticmethod
    def open(
        position_id: PositionId,
        symbol: Symbol,
        side: PositionSide,
        volume: PositiveVolume,
        entry_price: Price,
        currency: str = "USD",
    ) -> Position:
        return Position(
            position_id=position_id,
            symbol=symbol,
            side=side,
            volume=volume,
            entry_price=entry_price,
            realized_pnl=Money(Decimal("0"), currency),
            closed=False,
        )

    # Commands -----------------------------------------------------------------

    def close(self, exit_price: Price) -> Position:
        if self.closed:
            raise PositionAlreadyClosed("Position already closed")

        delta = exit_price.value - self.entry_price.value
        pnl_value = delta * self.volume.value * Decimal(self.side.sign())

        return replace(
            self,
            realized_pnl=Money(pnl_value, self.realized_pnl.currency),
            closed=True,
        )
