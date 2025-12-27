from enum import StrEnum


class OrderStatus(StrEnum):
    PENDING = "pending"
    ACKED = "acked"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
