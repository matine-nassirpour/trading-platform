from dataclasses import dataclass

from quantum.domain.risk.sizing.value_objects.position_volume import PositionVolume
from quantum.domain.risk.sizing.value_objects.risk_amount import RiskAmount
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class PositionSizingResult(ValueObject):
    """
    Canonical result of a successful sizing evaluation.

    risk_amount:
        Monetary amount actually allowed to be risked.

    volume:
        Final risk-approved executable volume.

    This object does not create an order.
    """

    risk_amount: RiskAmount
    volume: PositionVolume

    def _validate_semantics(self) -> None:
        if not isinstance(self.risk_amount, RiskAmount):
            raise InvariantViolation("PositionSizingResult.risk_amount invalid")

        if not isinstance(self.volume, PositionVolume):
            raise InvariantViolation("PositionSizingResult.volume invalid")
