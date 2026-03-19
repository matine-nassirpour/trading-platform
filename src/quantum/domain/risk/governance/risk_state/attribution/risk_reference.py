from dataclasses import dataclass

from quantum.domain.shared_kernel.ddd.value_objects.value_object import ValueObject
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class RiskReference(ValueObject):
    """
    Opaque, stable identifier for a risk source.

    Examples:
    - "strategy:mean_reversion_v3"
    - "symbol:EURUSD"
    - "position:42"
    """

    value: str

    def _validate(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolation("RiskReference must be a string")

        if not self.value.strip():
            raise InvariantViolation("RiskReference must not be empty")
