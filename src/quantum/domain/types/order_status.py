from enum import StrEnum


class OrderStatus(StrEnum):
    """
    Canonical order lifecycle states (domain-level).
    """

    PENDING = "pending"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
