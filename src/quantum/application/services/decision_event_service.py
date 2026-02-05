from quantum.domain.decision.events.v1.decision_authorized_event import (
    DecisionAuthorizedEvent,
)
from quantum.domain.decision.events.v1.decision_rejected_event import (
    DecisionRejectedEvent,
)
from quantum.domain.decision.governance.decision_policy_result import (
    DecisionPolicyResult,
)
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId


class DecisionEventService:
    """
    Responsible for constructing domain events from policy results.
    """

    @staticmethod
    def event_from_result(
        intent_id: IntentId,
        result: DecisionPolicyResult,
    ):
        if result.authorized:
            return DecisionAuthorizedEvent(
                intent_id=intent_id,
                result=result,
            )

        return DecisionRejectedEvent(
            intent_id=intent_id,
            result=result,
        )
