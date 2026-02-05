from quantum.application.services.kill_switch_service import KillSwitchService


class TriggerKillSwitchUseCase:

    def __init__(self, service: KillSwitchService) -> None:
        self._service = service

    def execute(self, reason, detail=None) -> None:
        self._service.trigger(reason=reason, detail=detail)
