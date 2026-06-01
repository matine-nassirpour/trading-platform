from dataclasses import dataclass

from quantum.domain.decision.authorization.decision_authorization_reason_code import (
    DecisionAuthorizationReasonCode,
)
from quantum.domain.decision.authorization.decision_authorization_status import (
    DecisionAuthorizationStatus,
)
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId


@dataclass(frozen=True, slots=True)
class TradingDecisionCommandResult:
    """
    Minimal application result for mutation commands targeting TradingDecision.
    """

    decision_id: DecisionId


@dataclass(frozen=True, slots=True)
class TradingDecisionAuthorizationCommandResult:
    """
    Application result for authorization workflow.

    This result is read-model oriented and does not replace the persisted
    domain event as the source of truth.
    """

    decision_id: DecisionId
    status: DecisionAuthorizationStatus
    reason_code: DecisionAuthorizationReasonCode | None
