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

        v = self.value.strip().lower()

        if not _POLICY_ID_RE.fullmatch(v):
            raise InvariantViolation(
                "DecisionPolicyId must match pattern: [a-z][a-z0-9_:-]{2,63}"
            )

        object.__setattr__(self, "value", v)

    def __str__(self) -> str:
        return self.value
