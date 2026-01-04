from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.primitives.monetary_value_object import (
    MonetaryValueObject,
)
from quantum.domain.shared_kernel.value_objects.currency import Currency


@dataclass(frozen=True)
class Swap(MonetaryValueObject):
    """
    PnL resulting from swap / rollover.
    Can be positive or negative.
    """

    value: Decimal
    currency: Currency

    def _validate_semantics(self) -> None:
        pass
