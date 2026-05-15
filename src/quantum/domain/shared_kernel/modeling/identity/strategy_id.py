import re

from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject

_STRATEGY_ID_RE = re.compile(r"^[a-z][a-z0-9_]{2,50}$")


@dataclass(frozen=True, slots=True)
class StrategyId(ValueObject):
    """
    Canonical identifier of a trading strategy.

    IMPORTANT:
    This object does NOT normalize input.

    Accepted:
    - StrategyId("mean_reversion_intraday")

    Rejected:
    - StrategyId(" Mean_Reversion_Intraday ")
    - StrategyId("MEAN_REVERSION_INTRADAY")

    External normalization belongs to Anti-Corruption Layers.
    """

    value: str

    def _validate_semantics(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolation("StrategyId must be a string.")

        canonical = self.value.strip().lower()

        if self.value != canonical:
            raise InvariantViolation(
                f"StrategyId must already be canonical. "
                f"Got {self.value!r}, expected {canonical!r}. "
                "Normalization must happen outside the domain."
            )

        if not _STRATEGY_ID_RE.fullmatch(self.value):
            raise InvariantViolation(
                "StrategyId must match pattern: [a-z][a-z0-9_]{2,50}."
            )

    def __str__(self) -> str:
        return self.value
