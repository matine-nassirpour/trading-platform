from enum import StrEnum


class TimeInForce(StrEnum):
    GTC = "gtc"
    DAY = "day"
    SPECIFIED = "specified"
    SPECIFIED_DAY = "specified_day"
