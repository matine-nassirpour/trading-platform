from enum import StrEnum


class App(StrEnum):
    PYTHON_CORE = "python_core"
    EA_MQL5 = "ea_mql5"
    STREAMLIT_UI = "streamlit_ui"


class TradeAction(StrEnum):
    DEAL = "deal"
    PENDING = "pending"
    SLTP = "sltp"
    MODIFY = "modify"
    REMOVE = "remove"
    CLOSE_BY = "close_by"  # Close a position by an opposite one


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


class OrderFillingType(StrEnum):
    FOK = "fok"
    IOC = "ioc"
    RETURN = "return"


class TimeInForce(StrEnum):
    GTC = "gtc"
    DAY = "day"
    SPECIFIED = "specified"
    SPECIFIED_DAY = "specified_day"


class KillSwitchReason(StrEnum):
    RISK_LIMIT = "risk_limit"
    NETWORK = "network"
    BROKER_REJECTS = "broker_rejects"
    MANUAL = "manual"


class LatencyPhase(StrEnum):
    TERMINAL_PING = "terminal_ping"
    ORDER_CHECK = "order_check"
    ORDER_SEND = "order_send"
    ACK = "ack"
    FILL = "fill"


class DealEntry(StrEnum):
    IN = "in"
    OUT = "out"
    # (optional) IN_OUT for synthetic close-by, if needed


class DealReason(StrEnum):
    CLIENT = "client"  # user / algo
    MOBILE = "mobile"
    WEB = "web"
    SL = "sl"  # stop loss triggered
    TP = "tp"  # take profit triggered
    SO = "so"  # stop out
    ROLLOVER = "rollover"  # swap/rollover
    REVERSE = "reverse"  # reverse position
