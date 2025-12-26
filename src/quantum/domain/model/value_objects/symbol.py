import re

from typing import ClassVar

from pydantic import Field, field_validator

from quantum.domain.model.value_objects.base import ValueObject


class Symbol(ValueObject):
    value: str = Field(..., description="Trading symbol")

    _PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^[A-Z0-9._\-]{3,20}$")

    @field_validator("value")
    @classmethod
    def _normalize(cls, v: str) -> str:
        val = v.strip().upper()
        if not cls._PATTERN.match(val):
            raise ValueError(f"Invalid symbol format: {v}")
        return val
