from abc import ABC
from dataclasses import dataclass
from typing import ClassVar, TypeVar, final

from quantum.domain.risk_governance.breaches.risk_breach import RiskBreach
from quantum.domain.risk_governance.limits.risk_threshold_policy import (
    RiskThresholdPolicy,
)
from quantum.domain.risk_governance.services.threshold_breach_detector import (
    ThresholdBreachDetector,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.monetary.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)

B = TypeVar("B", bound="ThresholdRiskBreach")


@dataclass(frozen=True, slots=True)
class ThresholdRiskBreach(RiskBreach, ABC):
    """
    Abstract base for typed monetary threshold breaches.

    This class removes duplication while preserving nominal breach types:
    - DrawdownBreach
    - DailyLossBreach
    - ExposureBreach
    - NotionalBreach

    Concrete subclasses must define:
    - CURRENT_TYPE
    - LIMIT_TYPE
    """

    current: ContextualMonetaryAmount
    limit: ContextualMonetaryAmount

    CURRENT_TYPE: ClassVar[type[ContextualMonetaryAmount]]
    LIMIT_TYPE: ClassVar[type[ContextualMonetaryAmount]]

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if not isinstance(self.current, self.CURRENT_TYPE):
            raise InvariantViolation(
                f"{self.__class__.__name__}.current must be "
                f"{self.CURRENT_TYPE.__name__}"
            )

        if not isinstance(self.limit, self.LIMIT_TYPE):
            raise InvariantViolation(
                f"{self.__class__.__name__}.limit must be "
                f"{self.LIMIT_TYPE.__name__}"
            )

        if self.current.context != self.limit.context:
            raise InvariantViolation(f"{self.__class__.__name__} MoneyContext mismatch")

        if self.current.currency != self.limit.currency:
            raise InvariantViolation(f"{self.__class__.__name__} currency mismatch")

    @classmethod
    @final
    def detect(
        cls: type[B],
        *,
        current: ContextualMonetaryAmount,
        limit: ContextualMonetaryAmount,
        policy: RiskThresholdPolicy,
    ) -> B | None:
        return ThresholdBreachDetector.detect(
            current_value=current.value,
            limit_value=limit.value,
            policy=policy,
            breach_factory=lambda: cls(
                current=current,
                limit=limit,
                policy=policy,
            ),
        )
