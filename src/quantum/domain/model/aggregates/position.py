from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.model.exceptions import InvalidStateTransition
from quantum.domain.model.value_objects.identifiers import PositionId
from quantum.domain.model.value_objects.money import Money
from quantum.domain.model.value_objects.price import Price
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.volume import Volume


@dataclass
class Position:
    """
    Aggregate Root.
    """

    position_id: PositionId
    symbol: Symbol
    volume: Volume
    entry_price: Price
    realized_pnl: Money = Money(Decimal("0"))

    _closed: bool = False

    def close(self, exit_price: Price) -> None:
        if self._closed:
            raise InvalidStateTransition("Position already closed")

        pnl_value = (exit_price.value - self.entry_price.value) * self.volume.value
        self.realized_pnl = Money(pnl_value, self.realized_pnl.currency)
        self._closed = True

    @property
    def is_closed(self) -> bool:
        return self._closed
