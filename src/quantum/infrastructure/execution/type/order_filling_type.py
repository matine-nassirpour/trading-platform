from enum import StrEnum


class OrderFillingType(StrEnum):
    FOK = "fok"
    IOC = "ioc"
    RETURN = "return"
