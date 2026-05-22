import re

from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject

_POLICY_ID_RE = re.compile(r"^[a-z][a-z0-9_:-]{2,63}$")


@dataclass(frozen=True, slots=True)
class DecisionPolicyId(ValueObject):
    """
    Canonical identifier of a decision governance policy.

    Examples:
    - decision_default_v1
    - intraday_fx_policy
    - gov:decision_authorization_v3
    """

    value: str

    def _validate_semantics(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolation("DecisionPolicyId must be a string")

        canonical = self.value.strip().lower()

        if self.value != canonical:
            raise InvariantViolation(
                f"DecisionPolicyId must already be canonical. "
                f"Got {self.value!r}, expected {canonical!r}. "
                "Normalization must happen outside the domain."
            )

        if _POLICY_ID_RE.fullmatch(self.value) is None:
            raise InvariantViolation(
                "DecisionPolicyId must match pattern: [a-z][a-z0-9_:-]{2,63}"
            )

    def __str__(self) -> str:
        return self.value
