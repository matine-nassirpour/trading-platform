from dataclasses import dataclass

from quantum.domain.decision.governance.decision_policy_result import (
    DecisionPolicyResult,
)
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId


@dataclass(frozen=True, slots=True)
class RejectTradingIntentCommand:
    intent_id: IntentId
    result: DecisionPolicyResult
