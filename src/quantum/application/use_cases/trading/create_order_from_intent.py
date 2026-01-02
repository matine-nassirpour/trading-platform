class CreateOrderFromIntentUseCase:
    def __init__(self, intent_repo, event_publisher, uow):
        self._intent_repo = intent_repo
        self._event_publisher = event_publisher
        self._uow = uow

    def execute(self, command):
        with self._uow:
            intent = self._intent_repo.get(command.intent_id)
            if intent is None:
                raise RuntimeError("TradingIntent not found")

            intent = intent.create_order(
                order_id=command.order_id,
                order_type=command.order_type,
                volume=command.volume,
                at=command.at,
                sizing_model=command.sizing_model,
            )

            self._intent_repo.save(intent)
            self._event_publisher.publish(intent.events)
            self._uow.commit()
