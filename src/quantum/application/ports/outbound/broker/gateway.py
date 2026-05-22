from abc import abstractmethod
from typing import Protocol, runtime_checkable

from quantum.domain.trading.identity.broker_order_ref import BrokerOrderRef
from quantum.domain.trading.order.events.order_created_event import OrderCreatedEvent


@runtime_checkable
class BrokerGateway(Protocol):

    @abstractmethod
    def submit_order(self, event: OrderCreatedEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    def cancel_order(self, broker_order_ref: BrokerOrderRef) -> None:
        raise NotImplementedError
