from decimal import Decimal

from pydantic import Field

from quantum.domain.model.value_objects.base import ValueObject


class Money(ValueObject):
    value: Decimal = Field(..., description="Signed monetary amount")
