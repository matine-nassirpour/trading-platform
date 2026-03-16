from dataclasses import dataclass

from quantum.domain.risk.capital_reservation.capital_release_reason_code import (
    CapitalReleaseReasonCode,
)
from quantum.domain.risk.capital_reservation.capital_reservation_reserved_state import (
    CapitalReservationReservedState,
)
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True, slots=True)
class CapitalReservationReleasedState(CapitalReservationReservedState):
    """
    Previously reserved capital has been released back to the available budget.
    """

    release_reason_code: CapitalReleaseReasonCode
    released_at: EpochMs

    def _validate(self) -> None:
        super()._validate()

        if not isinstance(self.release_reason_code, CapitalReleaseReasonCode):
            raise InvariantViolation(
                "CapitalReservationReleasedState.release_reason_code invalid"
            )

        if not isinstance(self.released_at, EpochMs):
            raise InvariantViolation(
                "CapitalReservationReleasedState.released_at invalid"
            )

        if self.released_at.value < self.reserved_at.value:
            raise InvariantViolation(
                "CapitalReservationReleasedState.released_at must be >= reserved_at"
            )
