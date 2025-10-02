from enum import StrEnum


class App(StrEnum):
    PYTHON_CORE = "python_core"
    EA_MQL5 = "ea_mql5"
    STREAMLIT_UI = "streamlit_ui"


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


class PositionSide(StrEnum):
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class TimeInForce(StrEnum):
    IOC = "ioc"
    FOK = "fok"
    GTC = "gtc"


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
