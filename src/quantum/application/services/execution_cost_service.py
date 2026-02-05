from quantum.domain.trading.execution.settlement.execution_cost import ExecutionCost


class ExecutionCostService:

    @staticmethod
    def record_cost(cost: ExecutionCost) -> ExecutionCost:
        return cost
