import re

from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject

_BROKER_VENUE_ID_RE = re.compile(r"^[a-z][a-z0-9_]{2,50}$")


@dataclass(frozen=True, slots=True)
class BrokerVenueId(ValueObject):
    """
    Canonical broker / prop-firm / venue identifier.

    Examples:
    - ftmo_mt5
    - fundednext_mt5
    - icmarkets_live
    """

    value: str

    def _validate_semantics(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolation("BrokerVenueId must be a string")

        canonical = self.value.strip().lower()

        if not _BROKER_VENUE_ID_RE.fullmatch(canonical):
            raise InvariantViolation(
                "BrokerVenueId must match pattern: [a-z][a-z0-9_]{2,50}"
            )

        object.__setattr__(self, "value", canonical)

    def __str__(self) -> str:
        return self.value
