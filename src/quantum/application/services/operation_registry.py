from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TypeAlias

from quantum.application.contracts.execution_operation import ExecutionOperation
from quantum.application.contracts.execution_request import (
    CheckRequest,
    OrderRequest,
    QueryRequest,
)
from quantum.application.contracts.execution_result import ExecutionResult
from quantum.application.services.execution_service import ExecutionService

# Standard call signature for all operations
ExecutionFn: TypeAlias = Callable[[ExecutionService, object], ExecutionResult]


def _send_order(service: ExecutionService, req: OrderRequest) -> ExecutionResult:
    return service.send_order(req)


def _check_order(service: ExecutionService, req: CheckRequest) -> ExecutionResult:
    return service.check_order(req)


def _get_positions(service: ExecutionService, req: QueryRequest) -> ExecutionResult:
    return service.get_positions(req)


def _get_orders(service: ExecutionService, req: QueryRequest) -> ExecutionResult:
    return service.get_orders(req)


# ----- IMMUTABLE REGISTRY -----
OPERATION_REGISTRY: Mapping[ExecutionOperation, ExecutionFn] = {
    ExecutionOperation.SEND_ORDER: _send_order,
    ExecutionOperation.CHECK_ORDER: _check_order,
    ExecutionOperation.GET_POSITIONS: _get_positions,
    ExecutionOperation.GET_ORDERS: _get_orders,
}
