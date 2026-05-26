from quantum.domain.capital_management.allocation.capital_allocation_intent import (
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
    def assert_reserved_not_greater_than_requested(
        *,
        requested: CapitalAllocationIntent,
        reserved: CapitalAllocationIntent,
    ) -> None:
        if not isinstance(requested, CapitalAllocationIntent):
            raise InvariantViolation("requested must be CapitalAllocationIntent")

        if not isinstance(reserved, CapitalAllocationIntent):
            raise InvariantViolation("reserved must be CapitalAllocationIntent")

        if reserved.capital_fraction.value > requested.capital_fraction.value:
            raise InvariantViolation(
                "reserved capital_fraction must not exceed requested capital_fraction"
            )

        if reserved.risk_budget.value > requested.risk_budget.value:
            raise InvariantViolation(
                "reserved risk_budget must not exceed requested risk_budget"
            )

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
