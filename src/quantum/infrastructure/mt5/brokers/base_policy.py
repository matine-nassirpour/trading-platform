from abc import ABC, abstractmethod

from quantum.shared.types.execution_request import OrderRequest


class BrokerPolicy(ABC):
    @abstractmethod
    def validate(self, req: OrderRequest) -> None:
        """Raise on policy violation (spread, size, time windows, etc.)."""
