from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject
from quantum.domain.shared_kernel.value_objects.currency import Currency


@dataclass(frozen=True, slots=True)
class CurrencyPair(ValueObject):
    """
    Base / quote currency definition.

    Example: EUR / USD
    """

    base: Currency
    quote: Currency

    def _validate(self) -> None:
        if not isinstance(self.base, Currency):
            raise InvariantViolation("Base currency must be a Currency")

        if not isinstance(self.quote, Currency):
            raise InvariantViolation("Quote currency must be a Currency")

        if self.base == self.quote:
            raise InvariantViolation("Base and quote currency must differ")
