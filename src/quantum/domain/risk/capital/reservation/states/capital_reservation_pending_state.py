from dataclasses import dataclass

from quantum.domain.risk.capital.allocation.capital_allocation_intent import (
    CapitalAllocationIntent,
)
from quantum.domain.risk.capital.reservation.states.capital_reservation_state_base import (
    CapitalReservationStateBase,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.identity.intent_id import IntentId
from quantum.domain.shared_kernel.identity.strategy_id import StrategyId
from quantum.domain.shared_kernel.temporal.epoch_ms import EpochMs


@dataclass(frozen=True, slots=True)
class CapitalReservationPendingState(CapitalReservationStateBase):
    """
    Reservation has been requested but not yet decided by risk/capital policy.
    """

    intent_id: IntentId
    strategy_id: StrategyId
    requested_allocation: CapitalAllocationIntent
    requested_at: EpochMs

    def _validate(self) -> None:
        super()._validate()

        if self.last_sequence.is_initial():
            raise InvariantViolation(
                "Pending CapitalReservation cannot have initial sequence"
            )

        if not isinstance(self.intent_id, IntentId):
            raise InvariantViolation("CapitalReservationPendingState.intent_id invalid")

        if not isinstance(self.strategy_id, StrategyId):
            raise InvariantViolation(
                "CapitalReservationPendingState.strategy_id invalid"
            )

        if not isinstance(self.requested_allocation, CapitalAllocationIntent):
            raise InvariantViolation(
                "CapitalReservationPendingState.requested_allocation invalid"
            )

        if not isinstance(self.requested_at, EpochMs):
            raise InvariantViolation(
                "CapitalReservationPendingState.requested_at invalid"
            )
