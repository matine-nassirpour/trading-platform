from quantum.application.services.order_service import OrderService


class RegisterOrderFillUseCase:

    def __init__(self, service: OrderService):
        self._service = service

    def execute(self, order_id, fill):
        self._service.register_fill(order_id, fill)
