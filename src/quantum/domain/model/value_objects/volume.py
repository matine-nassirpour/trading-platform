from decimal import Decimal

from pydantic import Field

from quantum.domain.model.value_objects.base import ValueObject


class Volume(ValueObject):
    value: Decimal = Field(..., gt=0, description="Strictly positive volume")
