from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.decision.identity.decision_identity import DecisionIdentity
from quantum.domain.decision.outcome.no_trade.no_trade_decision import NoTradeDecision
from quantum.domain.market.instrument.identity.symbol import Symbol


@dataclass(frozen=True, slots=True)
class RegisterNoTradeCommand(BaseCommand):
    symbol: Symbol
    decision_identity: DecisionIdentity
    outcome: NoTradeDecision
