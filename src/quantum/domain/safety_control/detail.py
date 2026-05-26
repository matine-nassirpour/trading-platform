import re

from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject

_DETAIL_RE = re.compile(r"^[a-z0-9][a-z0-9 ._:/#-]{0,255}$")


@dataclass(frozen=True, slots=True)
class KillSwitchDetail(ValueObject):
    """
    Human-readable canonical detail attached to a kill-switch trigger.

    This is optional audit context, not a machine decision code.
    """

    value: str

    def _validate_semantics(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolation("KillSwitchDetail must be a string")

        canonical = self.value.strip().lower()

        if not canonical:
            raise InvariantViolation("KillSwitchDetail must not be empty")

        if self.value != canonical:
            raise InvariantViolation(
                f"KillSwitchDetail must already be canonical. "
                f"Got {self.value!r}, expected {canonical!r}. "
                "Normalization must happen outside the domain."
            )

        if _DETAIL_RE.fullmatch(self.value) is None:
            raise InvariantViolation(
                "KillSwitchDetail contains unsupported characters or exceeds length"
            )

    def __str__(self) -> str:
        return self.value
