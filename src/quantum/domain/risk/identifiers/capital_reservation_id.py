from dataclasses import dataclass

from quantum.domain.shared_kernel.identifiers.aggregate_id import AggregateId


@dataclass(frozen=True, slots=True)
class CapitalReservationId(AggregateId):
    """
    Identity of the CapitalReservation aggregate (event stream id).
    """

    pass
