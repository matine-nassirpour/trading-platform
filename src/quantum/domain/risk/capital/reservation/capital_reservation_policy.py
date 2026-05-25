from quantum.domain.risk.capital.allocation.capital_allocation_intent import (
    CapitalAllocationIntent,
)
from quantum.domain.risk.capital.reservation.capital_budget_snapshot import (
    CapitalBudgetSnapshot,
)
from quantum.domain.risk.capital.reservation.reason_codes.capital_reservation_rejection_reason_code import (
    CapitalReservationRejectionReasonCode,
)
from quantum.domain.shared_kernel.modeling.services.domain_service import DomainService


class CapitalReservationPolicy(DomainService):
    """
    Pure capital reservation policy.

    This object answers:
        "Can this allocation be reserved given the remaining budget?"
    """

    __slots__ = ()

    @staticmethod
    def evaluate(
        *,
        requested_allocation: CapitalAllocationIntent,
        budget: CapitalBudgetSnapshot,
    ) -> CapitalReservationRejectionReasonCode | None:
        if (
            requested_allocation.capital_fraction.value
            > budget.remaining_capital_fraction()
        ):
            return CapitalReservationRejectionReasonCode.capital_capacity_exhausted()

        if requested_allocation.risk_budget.value > budget.remaining_risk_budget():
            return CapitalReservationRejectionReasonCode.insufficient_risk_budget()

        return None
