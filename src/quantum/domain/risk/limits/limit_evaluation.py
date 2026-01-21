from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.risk.limits.drawdown_limit import DrawdownLimit
from quantum.domain.risk.limits.exposure_limit import ExposureLimit
from quantum.domain.risk.limits.leverage_limit import LeverageLimit
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class LimitEvaluationResult:
    """
    Result of a risk limit evaluation.
    """

    passed: bool
    reason: str


class RiskLimitEvaluator:
    """
    Canonical risk limit evaluation engine.

    This class:
    - does NOT mutate state
    - does NOT know about execution
    - is 100% deterministic
    """

    @staticmethod
    def check_exposure(
        *,
        current_exposure: Decimal,
        limit: ExposureLimit,
    ) -> LimitEvaluationResult:
        if current_exposure > limit.value:
            return LimitEvaluationResult(
                passed=False,
                reason="Exposure limit exceeded",
            )

        return LimitEvaluationResult(
            passed=True,
            reason="Exposure within limits",
        )

    @staticmethod
    def check_drawdown(
        *,
        current_drawdown: Decimal,
        limit: DrawdownLimit,
    ) -> LimitEvaluationResult:
        if current_drawdown > limit.value:
            return LimitEvaluationResult(
                passed=False,
                reason="Drawdown limit exceeded",
            )

        return LimitEvaluationResult(
            passed=True,
            reason="Drawdown within limits",
        )

    @staticmethod
    def check_leverage(
        *,
        exposure: Decimal,
        equity: Decimal,
        limit: LeverageLimit,
    ) -> LimitEvaluationResult:
        if equity <= Decimal("0"):
            raise InvariantViolation("Equity must be positive to compute leverage")

        leverage = exposure / equity

        if leverage > limit.value:
            return LimitEvaluationResult(
                passed=False,
                reason="Leverage limit exceeded",
            )

        return LimitEvaluationResult(
            passed=True,
            reason="Leverage within limits",
        )
