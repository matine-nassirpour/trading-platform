import logging
import os
import platform
import socket

from pathlib import Path

import streamlit as st

from runtime.runtime_composer import compose_runtime

from quantum.infrastructure.config.runtime.manager import ConfigManager
from quantum.infrastructure.config.runtime.state.ready_cache import ReadyStateCache
from quantum.infrastructure.observability.context.correlation_id import (
    correlation_context,
)

logger = logging.getLogger("quantum.app")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Cached runtime initialization (safety-critical: executed once)             │
# ╰────────────────────────────────────────────────────────────────────────────╯
@st.cache_resource
def _load_runtime():
    """Load and freeze the Quantum Runtime (cached once)."""
    runtime = compose_runtime()
    runtime.initialize_observability()
    return runtime


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Sections                                                                   │
# ╰────────────────────────────────────────────────────────────────────────────╯
def render_fingerprint_section() -> None:
    st.subheader("📌 Runtime Fingerprint")

    fp = ReadyStateCache._fingerprint

    st.code(fp, language="text")


def render_runtime_overview(runtime) -> None:
    st.subheader("🧩 Runtime Overview")

    identity = runtime._make_identity()
    now_utc = runtime.time_provider.now_utc()

    overview = {
        "application": {
            "name": identity.service_name,
            "version": identity.service_version,
            "namespace": identity.service_namespace,
            "environment": identity.environment,
            "instance_id": identity.instance_id,
        },
        "runtime": {
            "pid": os.getpid(),
            "working_directory": str(Path.cwd()),
            "python_version": platform.python_version(),
        },
        "system": {
            "hostname": socket.gethostname(),
            "os": platform.platform(),
            "cpu_count": os.cpu_count(),
            "system_time_utc": now_utc.isoformat(),
            "timezone": "UTC",
        },
    }

    st.json(overview)


def render_core_settings() -> None:
    st.subheader("⚙️ Core Configuration")

    core = ConfigManager.load_core_cached().model_dump()

    st.json(core)


def render_logging_settings() -> None:
    st.subheader("📝 Logging Settings")

    logging_settings = ConfigManager.load_logging_cached().model_dump()

    st.json(logging_settings)


def render_tracing_settings() -> None:
    st.subheader("📡 Tracing Settings")

    tracing_settings = ConfigManager.load_tracing_cached().model_dump()

    st.json(tracing_settings)


def render_mt5_settings() -> None:
    st.subheader("💼 MT5 Settings")

    mt5_settings = ConfigManager.load_mt5_cached().model_dump()

    st.json(mt5_settings)


def render_env_snapshot() -> None:
    st.subheader("🌍 Effective Environment")

    state = ReadyStateCache.get()
    if state is None:
        st.error("Runtime state unavailable.")
        return

    st.json(state.env)


def render_orphans() -> None:
    st.subheader("🟣 Orphan Environment Variables")

    state = ReadyStateCache.get()
    if not state or not state.metadata:
        st.info("No orphan environment variables detected.")
        return

    orphans = state.metadata.get("orphans", [])
    if not orphans:
        st.success("No orphan variables 🎉")
    else:
        st.warning(f"{len(orphans)} orphan variables detected:")
        st.json(orphans)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Main Page Renderer                                                         │
# ╰────────────────────────────────────────────────────────────────────────────╯
def render_page() -> None:
    runtime = _load_runtime()

    st.title("🔍 Quantum Observability — Core Dashboard")
    st.write("Realtime supervision of the Quantum Runtime configuration.")
    st.divider()

    render_fingerprint_section()
    st.divider()

    render_runtime_overview(runtime)
    st.divider()

    render_core_settings()
    st.divider()

    render_logging_settings()
    st.divider()

    render_tracing_settings()
    st.divider()

    render_mt5_settings()
    st.divider()

    render_env_snapshot()
    st.divider()

    render_orphans()
    st.divider()

    with correlation_context():
        logger.warning(
            "⚠️ Streamlit démarre – handlers actifs ? %s", bool(logger.handlers)
        )

    if st.button("Générer un log"):
        logger.info("Test log depuis Streamlit")
        st.success("Log généré ! (vérifie tes fichiers / pipeline)")
