from decimal import Decimal

from pydantic import Field

from quantum.domain.model.value_objects.base import ValueObject


class Price(ValueObject):
    value: Decimal = Field(..., gt=0, description="Strictly positive price")
