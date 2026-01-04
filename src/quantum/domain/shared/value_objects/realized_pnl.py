from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared.primitives.monetary_value_object import MonetaryValueObject
from quantum.domain.shared.value_objects.currency import Currency


@dataclass(frozen=True)
class RealizedPnL(MonetaryValueObject):
    """
    Realized profit and loss from executed trades.
    """

    value: Decimal
    currency: Currency

    def _validate_semantics(self) -> None:
        # No restriction: PnL ∈ ℝ
        pass

    @staticmethod
    def zero(currency: Currency) -> RealizedPnL:
        return RealizedPnL(Decimal("0"), currency)
