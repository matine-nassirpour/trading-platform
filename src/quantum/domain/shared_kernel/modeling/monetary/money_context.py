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
    allowed_currencies: tuple[Currency, ...]

    def _validate_allowed_currencies(self) -> None:
        if not isinstance(self.allowed_currencies, tuple):
            raise InvariantViolation(
                "MoneyContext.allowed_currencies must be a tuple[Currency, ...]"
            )

        if not self.allowed_currencies:
            raise InvariantViolation(
                "MoneyContext.allowed_currencies must not be empty"
            )

        seen: set[str] = set()
        previous_value: str | None = None

        for currency in self.allowed_currencies:
            if not isinstance(currency, Currency):
                raise InvariantViolation(
                    "MoneyContext.allowed_currencies must contain only Currency, "
                    f"got {type(currency).__name__}"
                )

            current_value = currency.value

            if current_value in seen:
                raise InvariantViolation(
                    "MoneyContext.allowed_currencies must not contain duplicates"
                )

            if previous_value is not None and current_value <= previous_value:
                raise InvariantViolation(
                    "MoneyContext.allowed_currencies must be strictly sorted by "
                    "canonical currency value"
                )

            seen.add(current_value)
            previous_value = current_value

    def _validate_semantics(self) -> None:
        if not isinstance(self.reporting_currency, Currency):
            raise InvariantViolation(
                "MoneyContext.reporting_currency must be a Currency"
            )

        self._validate_allowed_currencies()

        if self.reporting_currency not in self.allowed_currencies:
            raise InvariantViolation(
                "MoneyContext.reporting_currency must be included in "
                "allowed_currencies"
            )
