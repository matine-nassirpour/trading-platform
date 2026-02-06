from abc import abstractmethod
from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.execution.order.order_type import OrderType
from quantum.domain.trading.execution.order.position_side import PositionSide


@runtime_checkable
class ExecutionGateway(Protocol):

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
