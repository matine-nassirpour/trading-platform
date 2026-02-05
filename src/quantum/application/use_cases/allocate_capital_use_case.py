from quantum.application.services.capital_allocation_service import (
    CapitalAllocationService,
)


class AllocateCapitalUseCase:

    def __init__(self, service: CapitalAllocationService) -> None:
        self._service = service

    def execute(self, intent):
        return self._service.validate(intent)
