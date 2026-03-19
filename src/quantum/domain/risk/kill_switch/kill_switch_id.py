from dataclasses import dataclass

from quantum.domain.shared_kernel.identity.aggregate_id import AggregateId


@dataclass(frozen=True, slots=True)
class KillSwitchStateId(AggregateId):
    """
    Identity of the KillSwitchState aggregate (event stream id).
    """

    pass
