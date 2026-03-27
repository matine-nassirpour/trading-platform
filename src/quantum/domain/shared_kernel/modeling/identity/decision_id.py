from dataclasses import dataclass

from quantum.domain.shared_kernel.modeling.identity.aggregate_id import AggregateId


@dataclass(frozen=True, slots=True)
class DecisionId(AggregateId):
    """Identity of the TradingDecision aggregate (event stream id)."""

    pass
