from enum import StrEnum


class OrderType(StrEnum):
    BUY = "buy"
    SELL = "sell"
    BUY_LIMIT = "buy_limit"
    SELL_LIMIT = "sell_limit"
    BUY_STOP = "buy_stop"
    SELL_STOP = "sell_stop"
    BUY_STOP_LIMIT = "buy_stop_limit"
    SELL_STOP_LIMIT = "sell_stop_limit"
    CLOSE_BY = "close_by"  # Order for closing a position by an opposite one

    def requires_price(self) -> bool:
        return self not in {OrderType.BUY, OrderType.SELL}
