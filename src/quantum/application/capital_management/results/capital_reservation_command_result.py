from dataclasses import dataclass

from quantum.domain.capital_management.allocation.capital_allocation_intent import (
    CapitalAllocationIntent,
)
from quantum.domain.capital_management.reservation.capital_reservation_id import (
    CapitalReservationId,
)
from quantum.domain.capital_management.reservation.reason_codes.capital_reservation_rejection_reason_code import (
    CapitalReservationRejectionReasonCode,
)


@dataclass(frozen=True, slots=True)
class CapitalReservationCommandResult:
    """Base application result for commands targeting CapitalReservation."""

    reservation_id: CapitalReservationId


@dataclass(frozen=True, slots=True)
class RequestCapitalReservationResult(CapitalReservationCommandResult):
    """Result for capital reservation request workflow."""


@dataclass(frozen=True, slots=True)
class ReserveCapitalResult(CapitalReservationCommandResult):
    """
    Result for reserve workflow.

    The domain may accept or reject the reservation.
    """

    is_accepted: bool
    reserved_allocation: CapitalAllocationIntent | None
    rejection_reason_code: CapitalReservationRejectionReasonCode | None


@dataclass(frozen=True, slots=True)
class RejectCapitalReservationResult(CapitalReservationCommandResult):
    """Result for explicit rejection workflow."""

    reason_code: CapitalReservationRejectionReasonCode


@dataclass(frozen=True, slots=True)
class ReleaseCapitalReservationResult(CapitalReservationCommandResult):
    """Result for release workflow."""


@dataclass(frozen=True, slots=True)
class ConsumeCapitalReservationResult(CapitalReservationCommandResult):
    """Result for consume workflow."""
