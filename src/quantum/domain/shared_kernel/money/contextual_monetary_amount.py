from abc import ABC
from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.money_context import MoneyContext
from quantum.domain.shared_kernel.primitives.monetary_amount import MonetaryAmount
from quantum.domain.shared_kernel.value_objects.currency import Currency


@dataclass(frozen=True)
class ContextualMonetaryAmount(MonetaryAmount, ABC):
    """
    Monetary amount bound to a specific MoneyContext.

    This prevents cross-currency contamination at the system level.
    """

    value: Decimal
    currency: Currency
    context: MoneyContext

    def _validate_semantics(self) -> None:
        if not isinstance(self.context, MoneyContext):
            raise InvariantViolation("ContextualMonetaryAmount requires a MoneyContext")

        if self.currency != self.context.reporting_currency:
            raise InvariantViolation(
                f"Currency {self.currency} does not match MoneyContext {self.context.reporting_currency}"
            )
