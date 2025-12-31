from enum import StrEnum


class OrderCheckOutcome(StrEnum):
    ACCEPTED = "accepted"
    INSUFFICIENT_MARGIN = "insufficient_margin"
    INVALID_PRICE = "invalid_price"
    INVALID_VOLUME = "invalid_volume"
    MARKET_CLOSED = "market_closed"
    UNKNOWN_ERROR = "unknown_error"
