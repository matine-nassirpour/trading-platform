from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.notional import Notional
from quantum.domain.shared_kernel.primitives.value_object import ValueObject
from quantum.domain.shared_kernel.value_objects.symbol import Symbol


@dataclass(frozen=True, slots=True)
class PortfolioExposure(ValueObject):
    """
    Represents exposure for a symbol or portfolio slice.
    """

    symbol: Symbol
    notional: Notional
    leverage: Decimal

    def _validate(self) -> None:
        if not isinstance(self.symbol, Symbol):
            raise InvariantViolation("Exposure requires a Symbol")

        if not isinstance(self.notional, Notional):
            raise InvariantViolation("Exposure requires a Notional")

        if not isinstance(self.leverage, Decimal):
            raise InvariantViolation("Leverage must be Decimal")

        if self.leverage <= Decimal("0"):
            raise InvariantViolation("Leverage must be positive")
