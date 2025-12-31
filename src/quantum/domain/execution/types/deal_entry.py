from enum import StrEnum


class DealEntry(StrEnum):
    IN = "in"
    OUT = "out"
    # (optional) IN_OUT for synthetic close-by, if needed
