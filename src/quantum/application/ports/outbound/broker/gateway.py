from abc import abstractmethod
from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.identifiers.order_id import OrderId
from quantum.domain.trading.events.v1.order.order_created_event import OrderCreatedEvent


@runtime_checkable
class BrokerGateway(Protocol):

    @abstractmethod
    def submit_order(self, event: OrderCreatedEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    def cancel_order(self, order_id: OrderId) -> None:
        raise NotImplementedError
