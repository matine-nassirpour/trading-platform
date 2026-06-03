from enum import Enum, auto


class EmptyEventPolicy(Enum):
    """
    Defines how an aggregate command handler behaves when domain execution
    returns no domain events.
    """

    FORBID = auto()
    ALLOW_NOOP = auto()
