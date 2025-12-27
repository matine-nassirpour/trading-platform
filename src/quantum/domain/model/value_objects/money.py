from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.model.value_objects.base import ValueObject


@dataclass(frozen=True)
class Money(ValueObject):
    value: Decimal
