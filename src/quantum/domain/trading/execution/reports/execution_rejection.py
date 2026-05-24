import re

from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject

_REJECTION_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{2,63}$")


@dataclass(frozen=True, slots=True)
class ExecutionRejection(ValueObject):
    """
    Typed rejection payload.

    code:
        canonical machine-readable rejection code.

    description:
        human-readable diagnostic text, already sanitized by ACL.
    """

    code: str
    description: str

    def _validate_semantics(self) -> None:
        if not isinstance(self.code, str):
            raise InvariantViolation("ExecutionRejection.code must be a string")

        canonical_code = self.code.strip().lower()

        if self.code != canonical_code:
            raise InvariantViolation(
                f"ExecutionRejection.code must already be canonical. "
                f"Got {self.code!r}, expected {canonical_code!r}. "
                "Normalization must happen outside the domain."
            )

        if _REJECTION_CODE_RE.fullmatch(self.code) is None:
            raise InvariantViolation(
                "ExecutionRejection.code must match pattern: [a-z][a-z0-9_]{2,63}"
            )

        if not isinstance(self.description, str):
            raise InvariantViolation("ExecutionRejection.description must be a string")

        if not self.description.strip():
            raise InvariantViolation("ExecutionRejection.description must not be blank")
