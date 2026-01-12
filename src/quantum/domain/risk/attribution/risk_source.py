from dataclasses import dataclass

from quantum.domain.risk.attribution.risk_reference import RiskReference
from quantum.domain.risk.attribution.risk_source_type import RiskSourceType
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=False)
class RiskSource(ValueObject):
    """
    Concrete origin of a risk.

    Examples:
    - strategy = mean_reversion_v3
    - instrument = EURUSD
    - position = PositionId(42)
    """

    type: RiskSourceType
    reference: RiskReference

    def _validate_semantics(self) -> None:
        if not isinstance(self.type, RiskSourceType):
            raise InvariantViolation("RiskSource requires a RiskSourceType")

        if not isinstance(self.reference, RiskReference):
            raise InvariantViolation("RiskSource requires a RiskReference")
