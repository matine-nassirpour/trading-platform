from abc import abstractmethod
from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.identifiers.order_id import OrderId
from quantum.domain.trading.execution.order.order import Order


@runtime_checkable
class OrderRepository(Protocol):

    @abstractmethod
    def load(self, order_id: OrderId) -> Order:
        raise NotImplementedError

    @abstractmethod
    def save(self, order: Order) -> None:
        raise NotImplementedError
