from dataclasses import dataclass
from typing import Any

from contracts.core.base import ContractModel


@dataclass(frozen=True)
class ConfigDiagnosticsResponse(ContractModel):
    schema_version: str
    ready: bool
    fingerprint: str | None
    ready_state: dict[str, Any] | None
    loader_snapshot: dict[str, Any] | None
    reserved_env_keys: dict[str, str | None]
    cache_matches_params: bool | None
    has_valid_cache: bool | None
    error: str | None
