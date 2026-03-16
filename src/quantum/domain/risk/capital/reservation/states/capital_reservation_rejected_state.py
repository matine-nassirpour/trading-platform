from dataclasses import dataclass

from quantum.domain.risk.capital.reservation.reason_codes.capital_reservation_rejection_reason_code import (
    CapitalReservationRejectionReasonCode,
)
from quantum.domain.risk.capital.reservation.states.capital_reservation_pending_state import (
    CapitalReservationPendingState,
)
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True, slots=True)
class CapitalReservationRejectedState(CapitalReservationPendingState):
    """
    Reservation has been explicitly rejected by risk/capital policy.
    """

    rejection_reason_code: CapitalReservationRejectionReasonCode
    rejected_at: EpochMs

    def _validate(self) -> None:
        super()._validate()

        if not isinstance(
            self.rejection_reason_code,
            CapitalReservationRejectionReasonCode,
        ):
            raise InvariantViolation(
                "CapitalReservationRejectedState.rejection_reason_code invalid"
            )

        if not isinstance(self.rejected_at, EpochMs):
            raise InvariantViolation(
                "CapitalReservationRejectedState.rejected_at invalid"
            )

        if self.rejected_at.value < self.requested_at.value:
            raise InvariantViolation(
                "CapitalReservationRejectedState.rejected_at must be >= requested_at"
            )
