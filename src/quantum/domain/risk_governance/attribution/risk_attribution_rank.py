from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class RiskAttributionRank(ValueObject):
    """
    Deterministic relevance rank for risk attribution.

    Semantics:
    - 1 = primary contributor
    - higher values = lower relevance
    - must be strictly positive
    """

    value: int

    def _validate_semantics(self) -> None:
        if type(self.value) is not int:
            raise InvariantViolation("RiskAttributionRank must be a strict integer")

        if self.value <= 0:
            raise InvariantViolation("RiskAttributionRank must be strictly positive")
