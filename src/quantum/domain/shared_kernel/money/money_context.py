from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject
from quantum.domain.shared_kernel.value_objects.currency import Currency


@dataclass(frozen=True, slots=True)
class MoneyContext(ValueObject):
    """
    Canonical monetary frame of reference for the trading desk.

    All monetary values must belong to exactly one MoneyContext.
    """

    reporting_currency: Currency
    allowed_currencies: frozenset[Currency]

    def _validate(self) -> None:
        if not isinstance(self.reporting_currency, Currency):
            raise InvariantViolation("MoneyContext requires a reporting Currency")

        if not self.allowed_currencies:
            raise InvariantViolation(
                "MoneyContext requires at least one allowed currency"
            )

        if self.reporting_currency not in self.allowed_currencies:
            raise InvariantViolation(
                "Reporting currency must be included in allowed_currencies"
            )
