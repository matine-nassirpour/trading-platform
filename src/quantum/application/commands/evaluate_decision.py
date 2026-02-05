from dataclasses import dataclass

from quantum.domain.decision.context.trading_context import TradingContext
from quantum.domain.decision.identity.decision_identity import DecisionIdentity
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId


@dataclass(frozen=True, slots=True)
class EvaluateDecisionCommand:
    intent_id: IntentId
    decision_identity: DecisionIdentity
    trading_context: TradingContext
