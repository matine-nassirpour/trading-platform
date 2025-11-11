from decimal import Decimal
from typing import Annotated

from pydantic import Field

PositiveDecimal = Annotated[Decimal, Field(gt=0)]
"""Strictly positive decimal number (> 0)."""

NonNegativeDecimal = Annotated[Decimal, Field(ge=0)]
"""Non-negative decimal number (≥ 0)."""

NegativeDecimal = Annotated[Decimal, Field(lt=0)]
"""Strictly negative decimal number (< 0)."""
