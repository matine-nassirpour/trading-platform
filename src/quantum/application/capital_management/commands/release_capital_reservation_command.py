from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.capital_management.reservation.capital_reservation_id import (
    CapitalReservationId,
)
from quantum.domain.capital_management.reservation.reason_codes.capital_release_reason_code import (
    CapitalReleaseReasonCode,
)


@dataclass(frozen=True, slots=True)
class ReleaseCapitalReservationCommand(BaseCommand):
    """Command: release previously reserved capital."""

    reservation_id: CapitalReservationId
    reason_code: CapitalReleaseReasonCode
