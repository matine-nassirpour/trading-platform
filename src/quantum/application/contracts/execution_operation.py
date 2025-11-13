from __future__ import annotations

from enum import Enum, auto


class ExecutionOperation(Enum):
    SEND_ORDER = auto()
    CHECK_ORDER = auto()
    GET_POSITIONS = auto()
    GET_ORDERS = auto()
