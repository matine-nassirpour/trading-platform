from enum import StrEnum


class PositionSide(StrEnum):
    LONG = "long"
    SHORT = "short"

    def sign(self) -> int:
        return 1 if self is PositionSide.LONG else -1
