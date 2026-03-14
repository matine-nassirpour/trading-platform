from abc import abstractmethod
from typing import Protocol, runtime_checkable

from quantum.domain.trading.events.v1.order.order_created_event import OrderCreatedEvent
from quantum.domain.trading.identifiers.broker_order_id import BrokerOrderId


@runtime_checkable
class BrokerGateway(Protocol):

    @abstractmethod
    def submit_order(self, event: OrderCreatedEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    def cancel_order(self, broker_order_id: BrokerOrderId) -> None:
        raise NotImplementedError
