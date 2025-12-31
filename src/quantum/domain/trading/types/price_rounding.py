from enum import StrEnum


class PriceRoundingMode(StrEnum):
    """
    Canonical directional rounding modes for executable prices.
    """

    FLOOR = "floor"  # toward lower price
    CEILING = "ceiling"  # toward higher price
    NEAREST = "nearest"  # banker / statistical (non-executable)
