class EvaluateRiskUseCase:
    def __init__(self, risk_repo, limits_provider, event_publisher, uow):
        self._risk_repo = risk_repo
        self._limits_provider = limits_provider
        self._event_publisher = event_publisher
        self._uow = uow

    def execute(self, command):
        from quantum.domain.risk.policies.risk_policy import RiskPolicy

        with self._uow:
            limits = self._limits_provider.get_limits()

            breaches = [
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
            ]

            for breach in filter(None, breaches):
                self._event_publisher.publish((breach,))

            self._uow.commit()
