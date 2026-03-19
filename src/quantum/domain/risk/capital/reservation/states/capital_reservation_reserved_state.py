from dataclasses import dataclass

from quantum.domain.risk.capital.allocation.capital_allocation_intent import (
    CapitalAllocationIntent,
)
from quantum.domain.risk.capital.reservation.states.capital_reservation_pending_state import (
    CapitalReservationPendingState,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.temporal.epoch_ms import EpochMs


@dataclass(frozen=True, slots=True)
class CapitalReservationReservedState(CapitalReservationPendingState):
    """
    Capital has been reserved and is now committed for downstream execution.
    """

    reserved_allocation: CapitalAllocationIntent
    reserved_at: EpochMs

    def _validate(self) -> None:
        super()._validate()

        if not isinstance(self.reserved_allocation, CapitalAllocationIntent):
            raise InvariantViolation(
                "CapitalReservationReservedState.reserved_allocation invalid"
            )

        if not isinstance(self.reserved_at, EpochMs):
            raise InvariantViolation(
                "CapitalReservationReservedState.reserved_at invalid"
            )

        if self.reserved_at.value < self.requested_at.value:
            raise InvariantViolation(
                "CapitalReservationReservedState.reserved_at must be >= requested_at"
            )
