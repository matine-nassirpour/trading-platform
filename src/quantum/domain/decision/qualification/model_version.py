import re

from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject

_VERSION_RE = re.compile(r"^v\d+(\.\d+){0,2}$")


@dataclass(frozen=True, slots=True)
class ModelVersion(ValueObject):
    """
    Canonical model / logic version.

    IMPORTANT:
    This object does NOT normalize input.
    Normalization belongs to Anti-Corruption Layers.

    Accepted:
    - ModelVersion("v1")
    - ModelVersion("v2.1")
    - ModelVersion("v3.4.2")

    Rejected:
    - ModelVersion(" V1 ")
    - ModelVersion("V2.1")
    - ModelVersion("v1.2.3.4")
    """

    value: str

    def _validate_semantics(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolation("ModelVersion must be a string")

        canonical = self.value.strip().lower()

        if self.value != canonical:
            raise InvariantViolation(
                f"ModelVersion must already be canonical. "
                f"Got {self.value!r}, expected {canonical!r}. "
                "Normalization must happen outside the domain."
            )

        if _VERSION_RE.fullmatch(self.value) is None:
            raise InvariantViolation(
                "ModelVersion must follow semantic pattern: vN(.N){0,2}"
            )

    def __str__(self) -> str:
        return self.value
