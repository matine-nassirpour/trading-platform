from dataclasses import dataclass

from quantum.domain.model.exceptions import InvariantViolation
from quantum.domain.model.value_objects.base import ValueObject
from quantum.domain.model.value_objects.price import Price
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.volume import Volume
from quantum.domain.types.enums import OrderType


@dataclass(frozen=True)
class OrderRequestSnapshot(ValueObject):
    symbol: Symbol
    order_type: OrderType
    volume: Volume
    price: Price | None = None
    sl: Price | None = None
    tp: Price | None = None

    def _validate(self) -> None:
        if self.price is None and self.order_type.requires_price():
            raise InvariantViolation("Price required for this order type")
