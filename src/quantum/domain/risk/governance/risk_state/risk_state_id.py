from dataclasses import dataclass

from quantum.domain.shared_kernel.identity.aggregate_id import AggregateId


@dataclass(frozen=True, slots=True)
class RiskStateId(AggregateId):
    """
    Identity of the RiskState aggregate (event stream id).
    """

    pass
