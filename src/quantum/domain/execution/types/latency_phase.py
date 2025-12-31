from enum import StrEnum


class LatencyPhase(StrEnum):
    TERMINAL_PING = "terminal_ping"
    ORDER_CHECK = "order_check"
    ORDER_SEND = "order_send"
    ACK = "ack"
    FILL = "fill"
