from decimal import Decimal


class Money:
    __slots__ = ("_value",)

    def __init__(self, value: Decimal) -> None:
        self._value = value  # signed by design (PnL, fees)

    @property
    def value(self) -> Decimal:
        return self._value
