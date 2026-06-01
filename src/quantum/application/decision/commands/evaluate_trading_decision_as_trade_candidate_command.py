from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.decision.trading_decision.trade_direction import TradeDirection
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId


@dataclass(frozen=True, slots=True)
class EvaluateTradingDecisionAsTradeCandidateCommand(BaseCommand):
    """
    Command: resolve a pending TradingDecision as a trade candidate.
    """

    decision_id: DecisionId
    trade_direction: TradeDirection
