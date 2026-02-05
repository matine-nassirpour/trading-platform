from quantum.application.dto.risk_dto import StrategyEligibilityDTO
from quantum.application.services.strategy_eligibility_service import (
    StrategyEligibilityService,
)


class EvaluateStrategyEligibilityUseCase:

    def __init__(self, service: StrategyEligibilityService) -> None:
        self._service = service

    def execute(self, strategy_id, at) -> StrategyEligibilityDTO:
        result = self._service.evaluate(strategy_id, at)

        return StrategyEligibilityDTO(
            eligible=result.eligible,
            reason=result.reason,
        )
