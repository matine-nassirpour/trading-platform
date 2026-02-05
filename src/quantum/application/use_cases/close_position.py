from quantum.application.services.position_service import PositionService


class ClosePositionUseCase:

    def __init__(self, service: PositionService):
        self._service = service

    def execute(self, position_id, exit_price, context):
        self._service.close(position_id, exit_price, context)
