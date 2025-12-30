import uuid

from dataclasses import dataclass

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.base import ValueObject


@dataclass(frozen=True)
class ExecutionId(ValueObject):
    """
    Canonical unique execution identifier.
    """

    value: uuid.UUID

    def _validate(self) -> None:
        if not isinstance(self.value, uuid.UUID):
            raise InvariantViolation("ExecutionId must be a UUID")
