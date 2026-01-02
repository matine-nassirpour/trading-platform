from quantum.application.dto.commands.evaluate_risk import EvaluateRiskCommand
from quantum.application.mappers.risk_breach_event_mapper import RiskBreachEventMapper
from quantum.application.ports.outbound.domain_event_publisher import (
    DomainEventPublisher,
)
from quantum.application.ports.outbound.unit_of_work import UnitOfWork
from quantum.domain.risk.policies.risk_policy import RiskPolicy


class EvaluateRiskUseCase:
    """
    Application use case responsible for evaluating desk-level risk
    and emitting domain events when limits are breached.
    """

    def __init__(
        self,
        *,
        risk_repo,
        limits_provider,
        event_publisher: DomainEventPublisher,
        uow: UnitOfWork,
    ) -> None:
        self._risk_repo = risk_repo
        self._limits_provider = limits_provider
        self._event_publisher = event_publisher
        self._uow = uow

    def execute(self, command: EvaluateRiskCommand) -> None:
        with self._uow:
            limits = self._limits_provider.get_limits()

            breaches = (
                RiskPolicy.evaluate_drawdown(
                    current_drawdown=command.current_drawdown,
                    limits=limits,
                ),
                RiskPolicy.evaluate_notional(
                    notional=command.notional,
                    limits=limits,
                ),
                RiskPolicy.evaluate_daily_loss(
                    daily_loss=command.daily_loss,
                    limits=limits,
                ),
            )

            events = tuple(
                RiskBreachEventMapper.to_event(
                    breach=breach,
                    at=command.at,
                )
                for breach in breaches
                if breach is not None
            )

            if events:
                self._event_publisher.publish(events)

            self._uow.commit()
