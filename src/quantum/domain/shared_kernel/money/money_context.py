from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.value_objects.currency import Currency


@dataclass(frozen=True)
class MoneyContext:
    """
    Canonical monetary frame of reference for the entire trading desk.

    Examples:
    - USD reporting
    - EUR reporting

    All monetary values must belong to exactly one MoneyContext.
    """

    reporting_currency: Currency

    def __post_init__(self) -> None:
        if not isinstance(self.reporting_currency, Currency):
            raise InvariantViolation("MoneyContext requires a Currency")
