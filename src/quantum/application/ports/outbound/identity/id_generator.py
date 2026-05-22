from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.event_sourcing.events.correlation_id import (
    CorrelationId,
)
from quantum.domain.shared_kernel.event_sourcing.events.event_id import EventId
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.trading.execution.fills.execution_id import ExecutionId
from quantum.domain.trading.identity.broker_order_ref import BrokerOrderRef
from quantum.domain.trading.identity.broker_position_ref import BrokerPositionRef


@runtime_checkable
class IdGenerator(Protocol):
    def new_event_id(self) -> EventId:
        raise NotImplementedError

    def new_correlation_id(self) -> CorrelationId:
        raise NotImplementedError

    def new_intent_id(self) -> DecisionId:
        raise NotImplementedError

    def new_order_id(self) -> BrokerOrderRef:
        raise NotImplementedError

    def new_position_ref(self) -> BrokerPositionRef:
        raise NotImplementedError

    def new_execution_id(self) -> ExecutionId:
        raise NotImplementedError
