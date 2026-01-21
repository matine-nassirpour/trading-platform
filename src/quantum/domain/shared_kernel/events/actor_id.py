from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class ActorId(ValueObject):
    """
    Identifies the logical actor responsible for an action.

    Examples:
        - "strategy:mean_reversion_v3"
        - "system:risk_engine"
        - "user:trader_42"
        - "scheduler:daily_close"
    """

    value: str

    def _validate(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolation("ActorId must be a string")

        if not self.value.strip():
            raise InvariantViolation("ActorId must not be empty")

        if ":" not in self.value:
            raise InvariantViolation(
                "ActorId must follow 'namespace:identifier' format"
            )

    def namespace(self) -> str:
        return self.value.split(":", 1)[0]

    def identifier(self) -> str:
        return self.value.split(":", 1)[1]
