from quantum.application.errors.not_found_errors import OrderNotFound


class CancelOrderUseCase:
    def __init__(self, order_repo, event_publisher, uow):
        self._order_repo = order_repo
        self._event_publisher = event_publisher
        self._uow = uow

    def execute(self, command):
        with self._uow:
            order = self._order_repo.get(command.order_id)
            if order is None:
                raise OrderNotFound(command.order_id)

            order = order.cancel()

            self._order_repo.save(order)
            self._event_publisher.publish(order.events)
            self._uow.commit()
