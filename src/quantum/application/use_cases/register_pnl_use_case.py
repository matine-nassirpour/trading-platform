from quantum.application.services.risk_state_service import RiskStateService


class RegisterPnLUseCase:

    def __init__(self, service: RiskStateService) -> None:
        self._service = service

    def execute(self, **kwargs) -> None:
        self._service.register_pnl(**kwargs)
