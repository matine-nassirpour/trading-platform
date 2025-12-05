import os
import platform
import socket

import requests
import streamlit as st

CONFIG_READINESS_URL = "http://127.0.0.1:8765/config-readiness"


def fetch_ready_config_state() -> dict | None:
    """
    Passive read-only retrieval of the Runtime READY state.
    """
    try:
        r = requests.get(CONFIG_READINESS_URL, timeout=1)
        data = r.json()
        data["_http_status_code"] = r.status_code
        return data
    except Exception:
        return None


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Sections                                                                   │
# ╰────────────────────────────────────────────────────────────────────────────╯
def render_fsm_status(status: str, fingerprint: str):
    st.title("🏁 CONFIGURATION STATE OVERVIEW")

    colors = {
        "ready": "green",
        "error": "red",
    }
    color = colors.get(status.lower(), "orange")

    st.markdown(
        f"### **FSM Status :** <span style='color:{color}'>**{status.upper()}**</span>",
        unsafe_allow_html=True,
    )

    st.markdown("### 🔐 Fingerprint Canonical (SHA-256)")
    st.code(fingerprint, language="text")


def render_runtime_overview_from_json(ready_json: dict) -> None:
    st.subheader("🧩 Runtime Overview")

    snap = ready_json.get("runtime_snapshot", {})
    settings = ready_json.get("ready_state", {}).get("settings", {})
    core = settings.get("core", {})

    identity = {
        "service_name": core.get("quantum_app_name"),
        "service_version": core.get("quantum_app_version"),
        "service_namespace": core.get("quantum_ns"),
        "environment": core.get("quantum_env"),
        "instance_id": core.get("quantum_instance_id", "unknown"),
    }

    overview = {
        "application": identity,
        "runtime": snap,
        "system": {
            "hostname": socket.gethostname(),
            "os": platform.platform(),
            "cpu_count": os.cpu_count(),
        },
    }

    st.json(overview)


def render_configuration_settings_from_json(settings: dict) -> None:
    st.subheader("Configuration Settings")

    with st.expander("⚙️ Core Configuration"):
        st.json(settings.get("core", {}))

    with st.expander("📝 Logging Settings"):
        st.json(settings.get("logging", {}))

    with st.expander("📡 Tracing Settings"):
        st.json(settings.get("tracing", {}))

    with st.expander("💼 MT5 Settings"):
        st.json(settings.get("mt5", {}))


def render_env_snapshot_from_json(env: dict, metadata: dict) -> None:
    with st.expander("🌍 Effective Environment"):
        st.json(env)

    with st.expander("📝 Metadata"):
        st.json(metadata)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Main Page Renderer                                                         │
# ╰────────────────────────────────────────────────────────────────────────────╯
def render_page() -> None:
    ready_config_state = fetch_ready_config_state()

    if ready_config_state is None:
        st.error("❌ Failed to reach Runtime Status API.")
        return

    status_code = ready_config_state.pop("_http_status_code", 200)

    if status_code != 200:
        st.error(
            f"❌ Runtime not READY: {ready_config_state.get('reason', 'Unknown reason')}"
        )
        st.code(ready_config_state, language="json")
        return

    # READY path (canonical structure)
    ready_state = ready_config_state.get("ready_state")
    if ready_state is None:
        st.error("❌ Missing ready_state in response.")
        st.code(ready_config_state, language="json")
        return

    # Settings, metadata, env
    env = ready_state.get("env", {})
    settings = ready_state.get("settings", {})
    metadata = ready_state.get("metadata", {})

    st.title("🔍 Quantum Observability — Core Dashboard")
    st.write("Realtime supervision of the Quantum Runtime configuration.")
    st.divider()

    # FSM status
    status = ready_state.get("status")
    fp = ready_config_state.get("fingerprint")
    render_fsm_status(status, fp)
    st.divider()

    # Runtime overview
    render_runtime_overview_from_json(ready_config_state)
    st.divider()

    render_configuration_settings_from_json(settings)
    st.divider()

    render_env_snapshot_from_json(env, metadata)
    st.divider()
