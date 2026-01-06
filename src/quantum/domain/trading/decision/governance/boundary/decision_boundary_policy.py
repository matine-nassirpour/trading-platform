from quantum.domain.trading.context.trading_context import TradingContext
from quantum.domain.trading.decision.governance.boundary.decision_boundary import (
    DecisionBoundary,
)
from quantum.domain.trading.decision.governance.boundary.decision_boundary_result import (
    DecisionBoundaryResult,
)
from quantum.domain.trading.decision.identity.decision_identity import DecisionIdentity


class DecisionBoundaryPolicy:
    """
    Canonical policy for evaluating Decision Boundaries.

    HARD RULES:
    - Pure
    - Deterministic
    - No side effects
    - No runtime assumptions
    """

    @staticmethod
    def evaluate(
        *,
        boundary: DecisionBoundary,
        decision: DecisionIdentity,
        context: TradingContext,
    ) -> DecisionBoundaryResult:
        if decision.strategy_id != boundary.strategy_id:
            return DecisionBoundaryResult(
                authorized=False,
                reason="Strategy not authorized by this boundary",
            )

        if context.market_regime not in boundary.allowed_regimes:
            return DecisionBoundaryResult(
                authorized=False,
                reason="Market regime not authorized by this boundary",
            )

        return DecisionBoundaryResult(
            authorized=True,
            reason="Decision authorized by boundary",
        )
