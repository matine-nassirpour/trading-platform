from decimal import Decimal


class Volume:
    __slots__ = ("_value",)

    def __init__(self, value: Decimal) -> None:
        if value <= 0:
            raise ValueError("Volume must be strictly positive")
        self._value = value

    @property
    def value(self) -> Decimal:
        return self._value
