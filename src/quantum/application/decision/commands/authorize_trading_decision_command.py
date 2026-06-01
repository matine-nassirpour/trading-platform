from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId


@dataclass(frozen=True, slots=True)
class AuthorizeTradingDecisionCommand(BaseCommand):
    """
    Command: authorize or reject a trade-candidate TradingDecision.

    The application layer retrieves the applicable DecisionPolicy and
    StrategyLifecycle, then delegates the authorization decision to the domain.
    """

    decision_id: DecisionId
