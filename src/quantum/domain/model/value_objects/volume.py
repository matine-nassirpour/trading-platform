from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.model.value_objects.base import ValueObject
from quantum.domain.types.decimal import require_positive


@dataclass(frozen=True)
class Volume(ValueObject):
    value: Decimal

    def _validate(self) -> None:
        require_positive(self.value, "Volume")

    @classmethod
    def zero(cls) -> Volume:
        return cls(Decimal("0.0"))
