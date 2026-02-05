from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DecisionPolicyDTO:
    policy_id: str
    strategy_id: str
    allowed_regimes: set[str]
    requires_human_approval: bool
    experimental: bool
