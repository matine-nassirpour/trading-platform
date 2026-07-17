from enum import Enum, auto


class StepArgumentKind(Enum):
    NONE = auto()
    BUNDLE = auto()
    INFO_SAMPLER_STATE = auto()
    RATE_LIMIT_STATE = auto()
