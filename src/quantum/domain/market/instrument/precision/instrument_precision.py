from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class InstrumentPrecision(ValueObject):
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

    def _validate_semantics(self) -> None:
        self._validate_positive_decimal(self.price_increment, "price_increment")
        self._validate_positive_decimal(self.volume_increment, "volume_increment")
        self._validate_positive_decimal(self.price_scale, "price_scale")
        self._validate_positive_decimal(self.volume_scale, "volume_scale")
        self._validate_positive_decimal(self.money_scale, "money_scale")
