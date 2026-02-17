from enum import Enum, auto


class AggregateExistencePolicy(Enum):
    """
    Defines how AggregateCommandHandler behaves when aggregate is missing.
    """

    MUST_EXIST = auto()
    MUST_NOT_EXIST = auto()
    MAY_EXIST = auto()
