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

    Distinguishes:
    - increment: market constraint (multiple-of)
    - scale: representation / rounding constraint
    """

    symbol: Symbol

    price_increment: Decimal
    volume_increment: Decimal

    price_scale: Decimal  # e.g. Decimal("0.01")
    money_scale: Decimal  # e.g. Decimal("0.01")

    def _validate(self) -> None:
        self._validate_positive(self.price_increment, "price_increment")
        self._validate_positive(self.volume_increment, "volume_increment")
        self._validate_positive(self.price_scale, "price_scale")
        self._validate_positive(self.money_scale, "money_scale")

    @staticmethod
    def _validate_positive(value: Decimal, name: str) -> None:
        if not isinstance(value, Decimal):
            raise InvariantViolation(f"{name} must be a Decimal")
        if value <= Decimal("0"):
            raise InvariantViolation(f"{name} must be strictly positive")
