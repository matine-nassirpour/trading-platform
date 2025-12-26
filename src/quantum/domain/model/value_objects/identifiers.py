from dataclasses import dataclass


@dataclass(frozen=True)
class IntentId:
    value: str


@dataclass(frozen=True)
class OrderId:
    value: str


@dataclass(frozen=True)
class PositionId:
    value: str
