from quantum.application.commands.evaluate_risk_command import EvaluateRiskCommand
from quantum.application.ports.outbound.financial_state_provider import (
    FinancialStateProvider,
)
from quantum.application.ports.outbound.risk_event_publisher import RiskEventPublisher
from quantum.application.ports.outbound.risk_limits_provider import RiskLimitsRepository
from quantum.application.services.risk_evaluation_service import RiskEvaluationService


class EvaluateRiskUseCase:
    """
    Application use case:

    Evaluate current financial state against configured risk limits.
    """

    def __init__(
        self,
        limits_repository: RiskLimitsRepository,
        financials: FinancialStateProvider,
        publisher: RiskEventPublisher,
    ) -> None:
        self._limits_repository = limits_repository
        self._financials = financials
        self._publisher = publisher

    def execute(self, command: EvaluateRiskCommand) -> None:
        limits = self._limits_repository.current_limits()

        service = RiskEvaluationService(self._financials)

        breaches = service.evaluate(limits)

        for breach in breaches:
            self._publisher.publish_breach(breach)
