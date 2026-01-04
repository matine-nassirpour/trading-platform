from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.primitives.monetary_value_object import (
    MonetaryValueObject,
)
from quantum.domain.shared_kernel.value_objects.currency import Currency


@dataclass(frozen=True)
class UnrealizedPnL(MonetaryValueObject):
    """
    Unrealized Profit and Loss.

    Properties:
    - Derived, non-settled monetary variation
    - Can be positive, zero, or negative
    - Volatile by nature
    """

    value: Decimal
    currency: Currency

    def _validate_semantics(self) -> None:
        # No restriction: PnL ∈ ℝ
        pass
