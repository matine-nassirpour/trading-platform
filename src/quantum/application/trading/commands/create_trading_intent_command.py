from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.decision.context.trading_context import TradingContext
from quantum.domain.decision.identity.decision_identity import DecisionIdentity
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.value_objects.position_side import PositionSide
from quantum.domain.shared_kernel.value_objects.symbol import Symbol


@dataclass(frozen=True, slots=True)
class CreateTradingIntentCommand(BaseCommand):
    intent_id: IntentId
    symbol: Symbol
    side: PositionSide
    decision_identity: DecisionIdentity
    trading_context: TradingContext
