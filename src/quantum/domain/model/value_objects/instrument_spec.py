from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.base import ValueObject
from quantum.domain.model.value_objects.symbol import Symbol


@dataclass(frozen=True)
class InstrumentSpec(ValueObject):
    """
    Canonical tradable instrument specification.

    Distinguishes explicitly:
    - increment: market constraint (multiple-of)
    - scale: representation / rounding constraint
    """

    symbol: Symbol

    price_increment: Decimal
    volume_increment: Decimal

    price_scale: Decimal
    volume_scale: Decimal
    money_scale: Decimal

    @staticmethod
    def _validate_positive_decimal(value: Decimal, name: str) -> None:
        if not isinstance(value, Decimal):
            raise InvariantViolation(f"{name} must be a Decimal")
        if value <= Decimal("0"):
            raise InvariantViolation(f"{name} must be strictly positive")

    def _validate(self) -> None:
        self._validate_positive_decimal(self.price_increment, "price_increment")
        self._validate_positive_decimal(self.volume_increment, "volume_increment")

        self._validate_positive_decimal(self.price_scale, "price_scale")
        self._validate_positive_decimal(self.volume_scale, "volume_scale")
        self._validate_positive_decimal(self.money_scale, "money_scale")
