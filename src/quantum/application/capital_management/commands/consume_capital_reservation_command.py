from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.capital_management.reservation.capital_reservation_id import (
    CapitalReservationId,
)


@dataclass(frozen=True, slots=True)
class ConsumeCapitalReservationCommand(BaseCommand):
    """Command: mark previously reserved capital as consumed by downstream execution."""

    reservation_id: CapitalReservationId
