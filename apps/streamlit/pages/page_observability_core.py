import logging
import os
import platform
import socket

import streamlit as st

from runtime.runtime_composer import QuantumRuntime, compose_runtime

from quantum.infrastructure.config.runtime.fsm.model import (
    FSM_SCHEMA_VERSION,
    ConfigFSMState,
    ConfigLifecycleStatus,
)
from quantum.infrastructure.config.runtime.state.config_state import CONFIG_STATE
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
def render_fsm_status(status: ConfigLifecycleStatus):
    st.title("🏁 CONFIGURATION STATE OVERVIEW")

    colors = {
        ConfigLifecycleStatus.READY: "green",
        ConfigLifecycleStatus.ERROR: "red",
    }
    color = colors.get(status, "orange")
    st.markdown(
        f"### **FSM Status :** <span style='color:{color}'>**{status.value.upper()}**</span>",
        unsafe_allow_html=True,
    )
    st.badge(f"FSM Schema Version : {FSM_SCHEMA_VERSION}")

    st.markdown("### 🔐 Fingerprint Canonical (SHA-256)")
    fp = ReadyStateCache.get_fingerprint()
    st.code(fp, language="text")


def render_runtime_overview(runtime: QuantumRuntime) -> None:
    st.subheader("🧩 Runtime Overview")

    identity = runtime.identity
    runtime_snap = CONFIG_STATE.snapshot()
    now_utc = runtime.time_provider.now_utc()

    overview = {
        "application": {
            "name": identity.service_name,
            "version": identity.service_version,
            "namespace": identity.service_namespace,
            "environment": identity.environment,
            "instance_id": identity.instance_id,
        },
        "runtime": runtime_snap,
        "system": {
            "hostname": socket.gethostname(),
            "os": platform.platform(),
            "cpu_count": os.cpu_count(),
            "system_time_utc": now_utc.isoformat(),
            "timezone": "UTC",
        },
    }

    st.json(overview)


def render_configuration_settings(state: ConfigFSMState) -> None:
    settings = state.settings

    core = settings["core"]
    logging_settings = settings["logging"]
    tracing_settings = settings["tracing"]
    mt5_settings = settings["mt5"]

    st.subheader("Configuration Settings")

    with st.expander("⚙️ Core Configuration"):
        st.json(core)
    with st.expander("📝 Logging Settings"):
        st.json(logging_settings)
    with st.expander("📡 Tracing Settings"):
        st.json(tracing_settings)
    with st.expander("💼 MT5 Settings"):
        st.json(mt5_settings)


def render_env_snapshot(state: ConfigFSMState) -> None:
    with st.expander("🌍 Effective Environment"):
        st.json(state.env)
    with st.expander("📝 Metadata"):
        st.json(state.metadata)


def render_orphans(state: ConfigFSMState) -> None:
    st.subheader("🟣 Orphan Environment Variables")

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

    state = ReadyStateCache.get()
    if state is None:
        st.error("❌ READY state unavailable. Runtime not initialized.")
        return

    st.title("🔍 Quantum Observability — Core Dashboard")
    st.write("Realtime supervision of the Quantum Runtime configuration.")
    st.divider()

    render_fsm_status(state.status)
    st.divider()

    render_runtime_overview(runtime)
    st.divider()

    render_configuration_settings(state)
    render_env_snapshot(state)
    st.divider()

    render_orphans(state)
    st.divider()

    with correlation_context():
        logger.warning(
            "⚠️ Streamlit démarre – handlers actifs ? %s", bool(logger.handlers)
        )

    if st.button("Générer un log"):
        logger.info("Test log depuis Streamlit")
        st.success("Log généré ! (vérifie tes fichiers / pipeline)")
