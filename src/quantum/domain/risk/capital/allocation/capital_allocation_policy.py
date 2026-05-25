from quantum.domain.risk.capital.allocation.capital_allocation_intent import (
    CapitalAllocationIntent,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.services.domain_service import DomainService


class CapitalAllocationPolicy(DomainService):
    """
    Pure policy validating economic consistency of a CapitalAllocationIntent.
    """

    __slots__ = ()

    @staticmethod
    def assert_economically_consistent(
        allocation: CapitalAllocationIntent,
    ) -> None:
        if not isinstance(allocation, CapitalAllocationIntent):
            raise InvariantViolation("allocation must be CapitalAllocationIntent")

        if allocation.risk_budget.value > allocation.capital_fraction.value:
            raise InvariantViolation(
                "CapitalAllocationIntent is economically inconsistent: "
                "risk_budget must not exceed capital_fraction"
            )
