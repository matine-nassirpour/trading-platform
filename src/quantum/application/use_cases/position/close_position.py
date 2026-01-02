class ClosePositionUseCase:
    def __init__(self, repo, event_publisher, uow):
        self._repo = repo
        self._event_publisher = event_publisher
        self._uow = uow

    def execute(self, command):
        with self._uow:
            position = self._repo.get(command.position_id)
            if position is None:
                raise RuntimeError("Position not found")

            position = position.close(exit_price=command.exit_price)

            self._repo.save(position)
            self._event_publisher.publish(position.events)
            self._uow.commit()
