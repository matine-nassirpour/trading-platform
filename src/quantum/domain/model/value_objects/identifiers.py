from __future__ import annotations

import uuid

from typing import Any

from pydantic import Field, field_validator

from quantum.domain.model.value_objects.base import ValueObject


class IntentId(ValueObject):
    value: uuid.UUID

    @classmethod
    def new(cls) -> IntentId:
        return cls(value=uuid.uuid4())

    @field_validator("value", mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> uuid.UUID:
        if isinstance(v, uuid.UUID):
            return v
        return uuid.UUID(str(v))


class OrderId(ValueObject):
    value: int = Field(..., ge=1, description="Broker order identifier")


class DealId(ValueObject):
    value: int = Field(..., ge=1, description="Broker deal identifier")


class PositionId(ValueObject):
    value: int = Field(..., ge=1, description="Broker position identifier")
