from dataclasses import dataclass

from quantum.domain.shared_kernel.identifiers.aggregate_id import AggregateId


@dataclass(frozen=True, slots=True)
class IntentId(AggregateId):
    """Identity of the TradingIntent aggregate (event stream id)."""

    pass
