from enum import StrEnum


class ExecutionType(StrEnum):
    NEW = "new"
    PARTIAL_FILL = "partial_fill"
    FILL = "fill"
    CANCEL = "cancel"
    REJECT = "reject"


class LiquiditySide(StrEnum):
    MAKER = "maker"
    TAKER = "taker"
    UNKNOWN = "unknown"
