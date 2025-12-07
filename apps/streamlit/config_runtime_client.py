"""
Streamlit-side client for the Quantum runtime configuration.

Responsibilities
----------------
- Initialize the same configuration subsystem as the Quantum runtime.
- Expose a minimal, read-only API to access validated CoreSettings.
- Provide a small typed view for the admin HTTP entrypoint configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from quantum.infrastructure.config.models.core import CoreSettings
from quantum.infrastructure.config.runtime.manager import ConfigManager
from quantum.infrastructure.config.validators.runtime import initialize_validators


@dataclass(frozen=True)
class AdminHTTPConfig:
    enabled: bool
    base_url: str | None


@lru_cache(maxsize=1)
def _initialize_and_load_core_settings() -> CoreSettings:
    """
    One-shot initialization of the runtime configuration FSM for the Streamlit process,
    and retrieval of validated CoreSettings.

    This mirrors the behavior of the runtime composition root, but:
    - It does NOT touch ReadyStateCache.
    - It is read-only from the perspective of the Streamlit app.
    """
    initialize_validators()
    ConfigManager.run_fsm(root=None, env_file=None)
    return ConfigManager.load_core_cached()


def get_core_settings() -> CoreSettings:
    """
    Public API for Streamlit components.

    Returns a validated CoreSettings instance, shared through an internal LRU cache.
    """
    return _initialize_and_load_core_settings()


@lru_cache(maxsize=1)
def get_admin_http_config() -> AdminHTTPConfig:
    """
    Build the admin HTTP config (enabled flag + base URL) using the same CoreSettings
    as the runtime.

    This guarantees that:
    - If QUANTUM_ADMIN_HTTP_* change in the config layer,
      the Streamlit UI will automatically follow.
    - No manual os.getenv / hard-coded port is required.
    """
    core = get_core_settings()

    if not core.quantum_admin_http_enabled:
        return AdminHTTPConfig(enabled=False, base_url=None)

    host = core.quantum_admin_http_host
    port = core.quantum_admin_http_port
    base_path = core.quantum_admin_http_base_path.strip()

    base_url = f"http://{host}:{port}"

    if base_path and base_path != "/":
        if not base_path.startswith("/"):
            base_path = "/" + base_path

        if len(base_path) > 1 and base_path.endswith("/"):
            base_path = base_path[:-1]
        base_url += base_path

    return AdminHTTPConfig(enabled=True, base_url=base_url)
