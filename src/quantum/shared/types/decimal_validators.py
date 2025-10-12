from decimal import Decimal
from typing import Annotated, TypeAlias

from pydantic import AfterValidator


def _gt_zero(x: Decimal) -> Decimal:
    if x <= 0:
        raise ValueError("must be > 0")
    return x


def _ge_zero(x: Decimal) -> Decimal:
    if x < 0:
        raise ValueError("must be >= 0")
    return x


def _lt_zero(x: Decimal) -> Decimal:
    if x >= 0:
        raise ValueError("must be < 0")
    return x


PositiveDecimal: TypeAlias = Annotated[Decimal, AfterValidator(_gt_zero)]
NonNegativeDecimal: TypeAlias = Annotated[Decimal, AfterValidator(_ge_zero)]
NegativeDecimal: TypeAlias = Annotated[Decimal, AfterValidator(_lt_zero)]
