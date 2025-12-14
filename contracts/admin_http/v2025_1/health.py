from dataclasses import dataclass

from contracts.core.base import ContractModel


@dataclass(frozen=True)
class HealthResponse(ContractModel):
    status: str
