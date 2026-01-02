from __future__ import annotations

from typing import Protocol, runtime_checkable

from quantum.domain.execution.value_objects.execution_id import ExecutionId
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId
from quantum.domain.trading.value_objects.identifiers.order_id import OrderId
from quantum.domain.trading.value_objects.identifiers.position_id import PositionId


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
