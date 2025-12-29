from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.base import ValueObject
from quantum.domain.model.value_objects.symbol import Symbol


@dataclass(frozen=True)
class InstrumentSpec(ValueObject):
    """
    Market convention for a tradable instrument.

    Defines all monetary and volume granularity.
    """

    symbol: Symbol
    price_tick: Decimal
    volume_step: Decimal
    money_scale: Decimal

    def _validate(self) -> None:
        if self.price_tick <= Decimal("0"):
            raise InvariantViolation("price_tick must be > 0")

        if self.volume_step <= Decimal("0"):
            raise InvariantViolation("volume_step must be > 0")

        if self.money_scale <= Decimal("0"):
            raise InvariantViolation("money_scale must be > 0")
