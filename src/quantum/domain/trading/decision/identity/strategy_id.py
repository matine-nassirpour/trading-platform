import re

from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject

_STRATEGY_ID_RE = re.compile(r"^[a-z][a-z0-9_]{2,50}$")


@dataclass(frozen=True)
class StrategyId(ValueObject):
    """
    Canonical identifier of a trading strategy.

    Examples:
    - mean_reversion_intraday
    - breakout_daily
    - carry_fx_v1
    """

    value: str

    def _validate(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolation("StrategyId must be a string")

        v = self.value.strip().lower()

        if not _STRATEGY_ID_RE.match(v):
            raise InvariantViolation(
                "StrategyId must match pattern: [a-z][a-z0-9_]{2,50}"
            )

        object.__setattr__(self, "value", v)

    def __str__(self) -> str:
        return self.value
