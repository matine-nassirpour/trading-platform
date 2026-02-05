from abc import ABC, abstractmethod

from quantum.domain.shared_kernel.identifiers.order_id import OrderId
from quantum.domain.trading.execution.order.order import Order


class OrderRepository(ABC):

    @abstractmethod
    def load(self, order_id: OrderId) -> Order:
        raise NotImplementedError

    @abstractmethod
    def save(self, order: Order) -> None:
        raise NotImplementedError
