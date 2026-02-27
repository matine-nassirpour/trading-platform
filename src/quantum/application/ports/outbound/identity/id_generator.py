from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.events.correlation_id import CorrelationId
from quantum.domain.shared_kernel.events.event_id import EventId
from quantum.domain.shared_kernel.identifiers.broker_order_id import BrokerOrderId
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.identifiers.position_id import PositionId
from quantum.domain.trading.execution.order.execution_id import ExecutionId


@runtime_checkable
class IdGenerator(Protocol):
    def new_event_id(self) -> EventId:
        raise NotImplementedError

    def new_correlation_id(self) -> CorrelationId:
        raise NotImplementedError

    def new_intent_id(self) -> IntentId:
        raise NotImplementedError

    def new_order_id(self) -> BrokerOrderId:
        raise NotImplementedError

    def new_position_id(self) -> PositionId:
        raise NotImplementedError

    def new_execution_id(self) -> ExecutionId:
        raise NotImplementedError
