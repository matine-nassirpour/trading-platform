from dataclasses import dataclass

from quantum.domain.trading.common.value_objects.volume import NonNegativeVolume
from quantum.domain.trading.order.aggregate import OrderId
from quantum.domain.trading.order.status.order_fill_status import OrderFillStatus
from quantum.domain.trading.order.status.order_lifecycle_status import (
    OrderLifecycleStatus,
)


@dataclass(frozen=True, slots=True)
class OrderCommandResult:
    """
    Base application result for commands targeting Order.
    """

    order_id: OrderId


@dataclass(frozen=True, slots=True)
class CreateOrderResult(OrderCommandResult):
    """
    Result for order creation workflow.
    """


@dataclass(frozen=True, slots=True)
class SubmitOrderResult(OrderCommandResult):
    """
    Result for order submission workflow.
    """


@dataclass(frozen=True, slots=True)
class AcknowledgeOrderResult(OrderCommandResult):
    """
    Result for order acknowledgement workflow.
    """


@dataclass(frozen=True, slots=True)
class AcceptOrderResult(OrderCommandResult):
    """
    Result for order acceptance workflow.
    """


@dataclass(frozen=True, slots=True)
class RejectOrderResult(OrderCommandResult):
    """
    Result for order rejection workflow.
    """


@dataclass(frozen=True, slots=True)
class ExpireOrderResult(OrderCommandResult):
    """
    Result for order expiration workflow.
    """


@dataclass(frozen=True, slots=True)
class CancelOrderResult(OrderCommandResult):
    """
    Result for order cancellation workflow.
    """


@dataclass(frozen=True, slots=True)
class RegisterOrderFillResult(OrderCommandResult):
    """
    Result for order fill registration workflow.

    This is an application convenience result.
    The persisted domain event remains the source of truth.
    """

    filled_volume: NonNegativeVolume
    fill_status: OrderFillStatus
    lifecycle_status: OrderLifecycleStatus
