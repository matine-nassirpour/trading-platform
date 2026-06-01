from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.capital_management.reservation.capital_reservation_id import (
    CapitalReservationId,
)
from quantum.domain.capital_management.reservation.reason_codes.capital_reservation_rejection_reason_code import (
    CapitalReservationRejectionReasonCode,
)


@dataclass(frozen=True, slots=True)
class RejectCapitalReservationCommand(BaseCommand):
    """Command: explicitly reject a pending capital reservation."""

    reservation_id: CapitalReservationId
    reason_code: CapitalReservationRejectionReasonCode
