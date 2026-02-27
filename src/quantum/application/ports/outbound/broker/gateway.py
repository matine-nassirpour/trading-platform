from abc import abstractmethod
from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.identifiers.broker_order_id import BrokerOrderId
from quantum.domain.trading.events.v1.order.order_created_event import OrderCreatedEvent


@runtime_checkable
class BrokerGateway(Protocol):

    @abstractmethod
    def submit_order(self, event: OrderCreatedEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    def cancel_order(self, order_id: BrokerOrderId) -> None:
        raise NotImplementedError
