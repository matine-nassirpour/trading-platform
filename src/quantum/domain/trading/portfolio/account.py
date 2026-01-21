from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject
from quantum.domain.shared_kernel.value_objects.currency import Currency


@dataclass(frozen=True, slots=True)
class Account(ValueObject):
    """
    Represents a financial trading account.

    This is NOT a broker account.
    This is a logical capital container.
    """

    account_id: str
    base_currency: Currency

    def _validate(self) -> None:
        if not isinstance(self.account_id, str) or not self.account_id.strip():
            raise InvariantViolation("Account ID must be a non-empty string")

        if not isinstance(self.base_currency, Currency):
            raise InvariantViolation("Account requires a base currency")
