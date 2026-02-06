from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DecisionIdentityDTO:
    strategy_id: str
    model_version: str
    source: str
    confidence_level: str
    confidence_rationale: str | None


@dataclass(frozen=True, slots=True)
class NoTradeDecisionDTO:
    reason: str
    rationale: str | None


@dataclass(frozen=True, slots=True)
class DecisionEvaluationResultDTO:
    authorized: bool
    reason: str
