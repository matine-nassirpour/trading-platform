from enum import Enum


class SystemStatus(str, Enum):
    """
    Contractual, external-facing runtime system status.
    This status is a PROJECTION of the internal runtime lifecycle FSM.
    """

    UP = "UP"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"
