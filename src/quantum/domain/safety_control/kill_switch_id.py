from dataclasses import dataclass

from quantum.domain.shared_kernel.modeling.identity.aggregate_id import AggregateId


@dataclass(frozen=True, slots=True)
class KillSwitchId(AggregateId):
    """
    Identity of the KillSwitchState aggregate (event stream id).
    """

    pass
