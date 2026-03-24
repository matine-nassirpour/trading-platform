from dataclasses import dataclass

from quantum.domain.risk.capital.reservation.states.capital_reservation_reserved_state import (
    CapitalReservationReservedState,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.temporal.epoch_ms import EpochMs


@dataclass(frozen=True, slots=True)
class CapitalReservationConsumedState(CapitalReservationReservedState):
    """
    Reserved capital has been consumed by downstream execution/commitment.

    This is terminal from the reservation aggregate perspective.
    """

    consumed_at: EpochMs

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if not isinstance(self.consumed_at, EpochMs):
            raise InvariantViolation(
                "CapitalReservationConsumedState.consumed_at invalid"
            )

        if self.consumed_at.value < self.reserved_at.value:
            raise InvariantViolation(
                "CapitalReservationConsumedState.consumed_at must be >= reserved_at"
            )
