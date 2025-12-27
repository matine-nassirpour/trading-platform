from dataclasses import dataclass

from quantum.domain.model.value_objects.base import ValueObject


@dataclass(frozen=True)
class ExecutionRejection(ValueObject):
    code: str
    description: str

    def _validate(self) -> None:
        if not self.code:
            raise ValueError("Rejection code must not be empty")
