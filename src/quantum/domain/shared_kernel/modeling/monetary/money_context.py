from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.monetary.currency import Currency
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class MoneyContext(ValueObject):
    """
    Canonical monetary frame of reference for the trading desk.

    All monetary values must belong to exactly one MoneyContext.
    """

    reporting_currency: Currency
    allowed_currencies: frozenset[Currency]

    def _validate_semantics(self) -> None:
        if not isinstance(self.reporting_currency, Currency):
            raise InvariantViolation(
                "MoneyContext.reporting_currency must be a Currency"
            )

        if not isinstance(self.allowed_currencies, frozenset):
            raise InvariantViolation(
                "MoneyContext.allowed_currencies must be a frozenset[Currency]"
            )

        if not self.allowed_currencies:
            raise InvariantViolation(
                "MoneyContext.allowed_currencies must not be empty"
            )

        for c in self.allowed_currencies:
            if not isinstance(c, Currency):
                raise InvariantViolation(
                    f"MoneyContext.allowed_currencies must contain only Currency, got {type(c)}"
                )

        if self.reporting_currency not in self.allowed_currencies:
            raise InvariantViolation(
                "MoneyContext.reporting_currency must be included in allowed_currencies"
            )
