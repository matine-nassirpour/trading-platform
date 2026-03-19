from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.decision.governance.decision_policy import DecisionPolicy
from quantum.domain.decision.lifecycle.strategy_lifecycle import StrategyLifecycle
from quantum.domain.shared_kernel.identity.intent_id import IntentId
from quantum.domain.shared_kernel.temporal.epoch_ms import EpochMs


@dataclass(frozen=True, slots=True)
class EvaluateTradingIntentCommand(BaseCommand):
    intent_id: IntentId
    policy: DecisionPolicy
    lifecycle: StrategyLifecycle
    evaluated_at: EpochMs
