from quantum.application.services.execution_routing_service import (
    ExecutionRoutingService,
)


class PlaceOrderUseCase:

    def __init__(self, service: ExecutionRoutingService):
        self._service = service

    def execute(self, intent_id):
        self._service.route(intent_id)
