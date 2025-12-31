from enum import StrEnum


class DealReason(StrEnum):
    CLIENT = "client"  # user / algo
    MOBILE = "mobile"
    WEB = "web"
    SL = "sl"  # stop loss triggered
    TP = "tp"  # take profit triggered
    SO = "so"  # stop out
    ROLLOVER = "rollover"  # swap/rollover
    REVERSE = "reverse"  # reverse position
