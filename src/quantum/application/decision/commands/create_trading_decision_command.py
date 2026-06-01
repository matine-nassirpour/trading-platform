from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.decision.common.trading_context import TradingContext
from quantum.domain.decision.qualification.decision_qualification import (
    DecisionQualification,
)
from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId


@dataclass(frozen=True, slots=True)
class CreateTradingDecisionCommand(BaseCommand):
    """
    Command: create a new TradingDecision event stream.

    Application responsibility:
    - identify the target decision stream;
    - pass already canonical domain Value Objects to the aggregate;
    - preserve causal context through BaseCommand.context.

    Domain responsibility:
    - validate decision qualification;
    - validate trading context;
    - emit TradingDecisionCreatedEvent.
    """

    decision_id: DecisionId
    symbol: Symbol
    decision_qualification: DecisionQualification
    trading_context: TradingContext
