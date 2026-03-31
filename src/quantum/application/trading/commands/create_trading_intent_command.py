from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.decision.common.trading_context import TradingContext
from quantum.domain.decision.qualification.decision_qualification import (
    DecisionQualification,
)
from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.trading.execution.position_side import PositionSide


@dataclass(frozen=True, slots=True)
class CreateTradingIntentCommand(BaseCommand):
    intent_id: DecisionId
    symbol: Symbol
    side: PositionSide
    decision_identity: DecisionQualification
    trading_context: TradingContext
