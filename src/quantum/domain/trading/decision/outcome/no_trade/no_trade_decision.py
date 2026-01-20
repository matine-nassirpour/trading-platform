from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject
from quantum.domain.trading.decision.outcome.no_trade.no_trade_reason import (
    NoTradeReason,
)


@dataclass(frozen=True, slots=True)
class NoTradeDecision(ValueObject):
    """
    Canonical NO-TRADE decision envelope.

    Answers:
        "WHY did we decide not to trade?"
    """

    reason: NoTradeReason
    rationale: str | None = None

    def _validate(self) -> None:
        if not isinstance(self.reason, NoTradeReason):
            raise InvariantViolation("NoTradeDecision requires a NoTradeReason")

        if self.rationale is not None:
            if not isinstance(self.rationale, str) or not self.rationale.strip():
                raise InvariantViolation(
                    "NoTradeDecision rationale must be a non-empty string"
                )
