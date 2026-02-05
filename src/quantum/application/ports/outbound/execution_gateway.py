from abc import ABC, abstractmethod

from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.execution.order.order_type import OrderType
from quantum.domain.trading.execution.order.position_side import PositionSide


class ExecutionGateway(ABC):

    @abstractmethod
    def send_order(
        self,
        *,
        symbol: Symbol,
        order_type: OrderType,
        side: PositionSide,
        volume: PositiveVolume,
    ) -> None:
        raise NotImplementedError
