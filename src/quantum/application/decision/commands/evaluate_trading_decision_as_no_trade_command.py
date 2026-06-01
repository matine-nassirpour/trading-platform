from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.decision.no_trade.no_trade_decision import NoTradeDecision
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId


@dataclass(frozen=True, slots=True)
class EvaluateTradingDecisionAsNoTradeCommand(BaseCommand):
    """
    Command: resolve a pending TradingDecision as an explicit no-trade decision.
    """

    decision_id: DecisionId
    no_trade_decision: NoTradeDecision
