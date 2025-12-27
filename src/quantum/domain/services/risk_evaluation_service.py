from __future__ import annotations

from quantum.domain.model.aggregates.risk_state import RiskState
from quantum.domain.model.value_objects.money import Money
from quantum.domain.model.value_objects.time import EpochMs


class RiskEvaluationService:
    """
    Domain Service coordinating risk evaluation logic.
    """

    @staticmethod
    def evaluate_pnl(
        risk_state: RiskState,
        pnl: Money,
        at: EpochMs,
    ) -> RiskState:
        """
        Applies a PnL delta to the risk state and returns
        the updated state (with possible events).
        """
        return risk_state.register_pnl(pnl, at)
