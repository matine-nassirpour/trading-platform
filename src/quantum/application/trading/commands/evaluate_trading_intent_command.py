from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.decision.authorization.decision_policy import DecisionPolicy
from quantum.domain.decision.authorization.strategy_lifecycle import StrategyLifecycle
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.temporal.epoch_ms import EpochMs


@dataclass(frozen=True, slots=True)
class EvaluateTradingIntentCommand(BaseCommand):
    intent_id: DecisionId
    policy: DecisionPolicy
    lifecycle: StrategyLifecycle
    evaluated_at: EpochMs
