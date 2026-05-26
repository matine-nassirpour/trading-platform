from dataclasses import dataclass

from quantum.domain.shared_kernel.modeling.identity.aggregate_id import AggregateId


@dataclass(frozen=True, slots=True)
class PositionSizingId(AggregateId):
    """Identity of the PositionSizing aggregate."""

    pass
