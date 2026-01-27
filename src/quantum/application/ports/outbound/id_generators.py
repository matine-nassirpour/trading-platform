from __future__ import annotations

from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.identifiers.order_id import OrderId
from quantum.domain.shared_kernel.identifiers.position_id import PositionId
from quantum.domain.trading.execution.order.execution_id import ExecutionId


@runtime_checkable
class IntentIdGenerator(Protocol):
    def new_intent_id(self) -> IntentId:
        raise NotImplementedError


@runtime_checkable
class OrderIdGenerator(Protocol):
    def new_order_id(self) -> OrderId:
        raise NotImplementedError


@runtime_checkable
class PositionIdGenerator(Protocol):
    def new_position_id(self) -> PositionId:
        raise NotImplementedError


@runtime_checkable
class ExecutionIdGenerator(Protocol):
    def new_execution_id(self) -> ExecutionId:
        raise NotImplementedError
