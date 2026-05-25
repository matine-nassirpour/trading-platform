from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class RiskScope(ValueObject):
    """
    Explicit risk limit scope.

    Examples:
    - desk:global
    - propfirm:ftmo
    - account:ftmo_challenge_001
    - strategy:mean_reversion_intraday
    """

    value: str

    def _validate_semantics(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolation("RiskScope must be a string")

        canonical = self.value.strip().lower()

        if not canonical:
            raise InvariantViolation("RiskScope must not be empty")

        if self.value != canonical:
            raise InvariantViolation(
                f"RiskScope must already be canonical. "
                f"Got {self.value!r}, expected {canonical!r}."
            )

        if ":" not in self.value:
            raise InvariantViolation(
                "RiskScope must use '<namespace>:<identifier>' format"
            )
