from __future__ import annotations

from typing import Any

from runtime.admin.diagnostics.config import ConfigDiagnosticsSnapshot
from runtime.presentation.safety import safe_expose


class ConfigDiagnosticsPresenter:
    """
    Canonical projection from internal runtime diagnostics snapshot
    to an external-facing, contract-compatible representation.
    """

    @staticmethod
    def present(snapshot: ConfigDiagnosticsSnapshot) -> dict[str, Any]:
        """
        Produce a contract-compatible payload.

        Rules:
        - NEVER raise
        - NEVER expose internal-only structures
        - NEVER mutate snapshot
        - Field mapping is EXPLICIT (no reflection / __dict__)
        """

        return {
            "schema_version": snapshot.schema_version,
            "ready": snapshot.ready,
            "fingerprint": snapshot.fingerprint,
            "ready_state": safe_expose(snapshot.ready_state),
            "loader_snapshot": safe_expose(snapshot.loader_snapshot),
            "reserved_env_keys": safe_expose(snapshot.reserved_env_keys),
            "cache_matches_params": snapshot.cache_matches_params,
            "has_valid_cache": snapshot.has_valid_cache,
            "error": snapshot.error,
        }
