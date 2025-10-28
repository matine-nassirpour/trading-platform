"""
Quantum Streamlit Runtime Configuration
────────────────────────────────────────
Provides a unified, thread-safe, and environment-aware configuration
bootstrap for Streamlit applications based on the Quantum Core stack.
"""

import threading
from dataclasses import dataclass
from pathlib import Path

from quantum.platform.config.models.core import CoreSettings
from quantum.platform.config.models.logging import LoggingSettings
from quantum.platform.config.models.mt5 import MT5Settings
from quantum.platform.config.models.tracing import TracingSettings
from quantum.platform.config.providers.env_loader import load_env
from quantum.platform.config.runtime.manager import ConfigManager
from quantum.platform.config.runtime.state import ConfigState

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Optional Streamlit integration (safe fallback if absent)                   │
# ╰────────────────────────────────────────────────────────────────────────────╯
try:
    import streamlit as st

    def _cache_resource(func):
        """Session-scoped cache decorator (active only in Streamlit runtime)."""
        return st.cache_resource(show_spinner=False)(func)

except ImportError:
    st = None

    def _cache_resource(func):
        """No-op fallback when Streamlit is unavailable (e.g., tests, CLI)."""
        return func


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Data container for strongly typed Quantum configuration bundle             │
# ╰────────────────────────────────────────────────────────────────────────────╯
@dataclass(frozen=True, slots=True)
class QuantumConfigBundle:
    """Aggregated configuration models for the Quantum runtime."""

    core: CoreSettings
    logging: LoggingSettings
    tracing: TracingSettings
    mt5: MT5Settings


# Global reentrant lock — guarantees idempotent initialization across threads.
_INIT_LOCK = threading.RLock()


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Low-level init (idempotent) — can be used outside Streamlit                │
# ╰────────────────────────────────────────────────────────────────────────────╯
def init_config(
    *,
    root: str | Path | None = None,
    env_file: str | Path | None = None,
    apply: bool = True,
    override: bool = False,
) -> QuantumConfigBundle:
    """
    Initialize Quantum configuration by loading environment layers and models.

    Thread-safe, idempotent, and framework-independent. Can be used in CLI tools,
    background workers, or tests without Streamlit.
    """
    with _INIT_LOCK:
        try:
            load_env(root=root, env_file=env_file, apply=apply, override=override)
        except Exception as exc:
            raise RuntimeError(
                f"[config_runtime] Failed to load environment (root={root}, env_file={env_file}): {exc}"
            ) from exc

        ConfigManager.clear_caches()

        core = ConfigManager.load(apply=apply)
        logging_cfg = ConfigManager.load_logging()
        tracing_cfg = ConfigManager.load_tracing()
        mt5_cfg = ConfigManager.load_mt5()

        return QuantumConfigBundle(
            core=core, logging=logging_cfg, tracing=tracing_cfg, mt5=mt5_cfg
        )


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Streamlit-facing cached accessor (1 call per user session)                 │
# ╰────────────────────────────────────────────────────────────────────────────╯
@_cache_resource
def get_config(
    *,
    root: str | Path | None = None,
    env_file: str | Path | None = None,
    apply: bool = True,
    override: bool = False,
) -> QuantumConfigBundle:
    """
    Retrieve the Quantum configuration bundle, cached per Streamlit user session.

    This wrapper ensures consistent and performant access to configuration models
    across Streamlit re-runs.
    """
    return init_config(root=root, env_file=env_file, apply=apply, override=override)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Refresh helpers (invalidate + reload)                                      │
# ╰────────────────────────────────────────────────────────────────────────────╯
def refresh_config(
    *,
    root: str | Path | None = None,
    env_file: str | Path | None = None,
    apply: bool = True,
    override: bool = False,
) -> QuantumConfigBundle:
    """
    Invalidate all configuration caches and reload the full environment stack.

    Used when the `.env` or `.env.local` files change during runtime,
    ensuring that Streamlit sessions and Quantum caches remain consistent.
    """
    ConfigManager.clear_caches()
    ConfigState.instance().reset()

    # Invalidate Streamlit cache if available
    if st is not None:
        try:
            get_config.clear()
        except AttributeError:
            pass

    # Reinitialize and return the updated bundle
    return get_config(root=root, env_file=env_file, apply=apply, override=override)
