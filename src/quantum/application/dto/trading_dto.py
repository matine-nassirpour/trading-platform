from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TradingIntentResultDTO:
    intent_id: str
    authorized: bool
    rejected: bool


@dataclass(frozen=True, slots=True)
class OrderResultDTO:
    order_id: str
    status: str


@dataclass(frozen=True, slots=True)
class PositionResultDTO:
    position_id: str
    closed: bool
