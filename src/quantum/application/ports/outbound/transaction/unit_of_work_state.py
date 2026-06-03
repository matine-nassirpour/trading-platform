from enum import Enum, auto


class UnitOfWorkState(Enum):
    NEW = auto()
    ACTIVE = auto()
    COMMITTED = auto()
    ROLLED_BACK = auto()
    DISPOSED = auto()
