from quantum.domain.risk.capital.capital_allocation_intent import (
    CapitalAllocationIntent,
)


class CapitalAllocationService:

    @staticmethod
    def validate(intent: CapitalAllocationIntent) -> CapitalAllocationIntent:
        # Purely domain-driven validation
        return intent
