from dataclasses import dataclass

from quantum.domain.risk.capital.reservation.states.capital_reservation_state_base import (
    CapitalReservationStateBase,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class CapitalReservationUninitializedState(CapitalReservationStateBase):
    """
    Represents the state BEFORE CapitalReservationRequestedEvent.

    This is the ONLY valid initial state.
    """

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if not self.last_sequence.is_initial():
            raise InvariantViolation(
                "Uninitialized CapitalReservation must have initial sequence"
            )
