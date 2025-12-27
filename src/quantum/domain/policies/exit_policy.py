from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.price import Price


@dataclass(frozen=True)
class ExitPolicy:
    """
    Validates SL/TP coherence.
    """

    @staticmethod
    def validate(
        sl: Price | None,
        tp: Price | None,
    ) -> None:
        if sl and sl.value <= Decimal("0"):
            raise InvariantViolation("Invalid stop loss")

        if tp and tp.value <= Decimal("0"):
            raise InvariantViolation("Invalid take profit")

        if sl and tp and sl.value == tp.value:
            raise InvariantViolation("SL and TP cannot be equal")
