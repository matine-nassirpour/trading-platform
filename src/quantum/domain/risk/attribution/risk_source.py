from dataclasses import dataclass
from typing import Any

from quantum.domain.risk.attribution.risk_source_type import RiskSourceType
from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.primitives.value_object import ValueObject


@dataclass(frozen=True)
class RiskSource(ValueObject):
    """
    Concrete origin of a risk.

    Examples:
    - strategy = mean_reversion_v3
    - instrument = EURUSD
    - position = PositionId(42)
    """

    type: RiskSourceType
    reference: Any  # intentionally opaque at domain level

    def _validate(self) -> None:
        if not isinstance(self.type, RiskSourceType):
            raise InvariantViolation("RiskSource requires a RiskSourceType")

        if self.reference is None:
            raise InvariantViolation("RiskSource reference must not be None")
