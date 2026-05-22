import re

from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject

_BROKER_ACCOUNT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{1,63}$")


@dataclass(frozen=True, slots=True)
class BrokerAccountId(ValueObject):
    """
    Canonical broker account identifier.

    This is not necessarily the raw broker login.
    External values must be mapped through an ACL.
    """

    value: str

    def _validate_semantics(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolation("BrokerAccountId must be a string")

        canonical = self.value.strip().lower()

        if not canonical:
            raise InvariantViolation("BrokerAccountId must not be empty")

        if self.value != canonical:
            raise InvariantViolation(
                f"BrokerAccountId must already be canonical. "
                f"Got {self.value!r}, expected {canonical!r}. "
                "Normalization must happen outside the domain."
            )

        if _BROKER_ACCOUNT_ID_RE.fullmatch(self.value) is None:
            raise InvariantViolation(
                "BrokerAccountId must match pattern: [a-z0-9][a-z0-9_.-]{1,63}"
            )

    def __str__(self) -> str:
        return self.value
