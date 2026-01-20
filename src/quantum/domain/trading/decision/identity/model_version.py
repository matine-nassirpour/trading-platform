import re

from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject

_VERSION_RE = re.compile(r"^v\d+(\.\d+){0,2}$")


@dataclass(frozen=True, slots=True)
class ModelVersion(ValueObject):
    """
    Canonical model / logic version.

    Examples:
    - v1
    - v2.1
    - v3.4.2
    """

    value: str

    def _validate(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolation("ModelVersion must be a string")

        v = self.value.strip().lower()

        if not _VERSION_RE.match(v):
            raise InvariantViolation(
                "ModelVersion must follow semantic pattern: vN(.N)*"
            )

        object.__setattr__(self, "value", v)

    def __str__(self) -> str:
        return self.value
