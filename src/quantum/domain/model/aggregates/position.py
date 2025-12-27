from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal

from quantum.domain.model.aggregates.base import AggregateRoot
from quantum.domain.model.exceptions import InvalidStateTransition
from quantum.domain.model.value_objects.identifiers import PositionId
from quantum.domain.model.value_objects.money import Money
from quantum.domain.model.value_objects.price import Price
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.volume import Volume
from quantum.domain.types.position_side import PositionSide


@dataclass(frozen=True)
class Position(AggregateRoot):
    position_id: PositionId
    symbol: Symbol
    side: PositionSide
    volume: Volume
    entry_price: Price
    realized_pnl: Money
    closed: bool = False

    @staticmethod
    def open(
        position_id: PositionId,
        symbol: Symbol,
        side: PositionSide,
        volume: Volume,
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

    def close(self, exit_price: Price) -> Position:
        if self.closed:
            raise InvalidStateTransition("Position already closed")

        delta = exit_price.value - self.entry_price.value
        pnl = delta * self.volume.value * Decimal(self.side.sign())

        return replace(
            self,
            realized_pnl=Money(pnl, self.realized_pnl.currency),
            closed=True,
        )
