from enum import StrEnum


class TradeAction(StrEnum):
    DEAL = "deal"
    PENDING = "pending"
    SLTP = "sltp"
    MODIFY = "modify"
    REMOVE = "remove"
    CLOSE_BY = "close_by"  # Close a position by an opposite one
