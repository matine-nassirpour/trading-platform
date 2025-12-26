from decimal import Decimal


class Price:
    __slots__ = ("_value",)

    def __init__(self, value: Decimal) -> None:
        if value <= 0:
            raise ValueError("Price must be strictly positive")
        self._value = value

    @property
    def value(self) -> Decimal:
        return self._value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Price) and self._value == other._value
