from quantum.domain.capital_management.allocation.capital_allocation_intent import (
    CapitalAllocationIntent,
)
from quantum.domain.position_sizing.value_objects.sizing_allocation import (
    SizingAllocation,
    SizingCapitalFraction,
    SizingRiskBudgetSlice,
)
from quantum.domain.position_sizing.value_objects.sizing_equity import SizingEquity
from quantum.domain.risk_governance.portfolio_state.equity import Equity


class PositionSizingInputMapper:
    @staticmethod
    def map_allocation(allocation: CapitalAllocationIntent) -> SizingAllocation:
        return SizingAllocation(
            capital_fraction=SizingCapitalFraction(allocation.capital_fraction.value),
            risk_budget=SizingRiskBudgetSlice(allocation.risk_budget.value),
        )

    @staticmethod
    def map_equity(equity: Equity) -> SizingEquity:
        return SizingEquity(
            value=equity.value,
            currency=equity.currency,
            context=equity.context,
        )
