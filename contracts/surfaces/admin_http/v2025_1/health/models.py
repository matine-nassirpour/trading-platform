from dataclasses import dataclass
from enum import Enum

from contracts.core.model import ContractModel


class HealthStatus(str, Enum):
    """
    Stable health contract enum.
    Values are intentionally coarse-grained.
    """

    OK = "OK"
    DEGRADED = "DEGRADED"
    FAILING = "FAILING"


@dataclass(frozen=True)
class HealthResponse(ContractModel):
    status: HealthStatus
