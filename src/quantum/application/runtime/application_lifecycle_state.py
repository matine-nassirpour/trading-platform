from enum import Enum, auto


class ApplicationLifecycleState(Enum):
    NEW = auto()
    STARTING = auto()
    STARTED = auto()
    STOPPING = auto()
    STOPPED = auto()
    FAILED = auto()
