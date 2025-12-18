from dataclasses import dataclass
from typing import Any

from contracts.core.model import ContractModel


@dataclass(frozen=True)
class ConfigReadyStateSnapshot(ContractModel):
    """
    Explicit snapshot of the consumable READY configuration state.

    This structure is:
    - diagnostics-only
    - immutable
    - fully specified for contract generation
    """

    fsm_status: str
    env: dict[str, str] | None
    settings: dict[str, Any] | None
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ConfigDiagnosticsResponse(ContractModel):
    """
    External, versioned contract for configuration diagnostics exposure.
    This model defines the stable API surface exposed to external clients.

    Any backward-incompatible change requires a new contract version.
    """

    schema_version: str
    is_consumable: bool
    fingerprint: str | None
    ready_state: ConfigReadyStateSnapshot | None
    loader_snapshot: dict[str, Any] | None
    reserved_env_keys: dict[str, str | None]
    cache_matches_params: bool | None
    has_valid_cache: bool | None
    error: str | None
