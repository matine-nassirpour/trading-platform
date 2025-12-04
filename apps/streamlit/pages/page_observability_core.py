import os
import platform
import socket

import requests
import streamlit as st

RUNTIME_OBS_HTTP = "http://127.0.0.1:8765/ready-state"


def load_ready_state() -> dict | None:
    """
    Passive read-only retrieval of the Runtime READY state.

    No side effects.
    No dependency on runtime internals.
    Fully Clean Architecture compliant.
    """
    try:
        r = requests.get(RUNTIME_OBS_HTTP, timeout=1)
        if r.status_code == 200:
            return r.json()
        return None
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
    ready = load_ready_state()

    if ready is None:
        st.error("❌ Failed to reach Runtime Observability API.")
        return

    # Detect NOT READY (503 path)
    if "status" in ready and ready["status"] != "ok":
        st.error(f"❌ Runtime not READY: {ready.get('reason', 'Unknown reason')}")
        st.code(ready, language="json")
        return

    # READY path (canonical structure)
    ready_state = ready.get("ready_state")
    if ready_state is None:
        st.error("❌ Missing ready_state in response.")
        st.code(ready, language="json")
        return

    # Settings, metadata, env
    env = ready_state.get("env", {})
    settings = ready_state.get("settings", {})
    metadata = ready_state.get("metadata", {})

    st.title("🔍 Quantum Observability — Core Dashboard")
    st.write("Realtime supervision of the Quantum Runtime configuration.")
    st.divider()

    # FSM status
    st.subheader("🏁 Configuration State")
    st.success("READY")
    st.write(f"Fingerprint : `{ready.get('fingerprint')}`")
    st.write(f"Schema version : `{ready.get('schema_version')}`")
    st.write(f"Timestamp : `{ready.get('timestamp_utc')}`")
    st.divider()

    # Runtime overview
    render_runtime_overview_from_json(ready)
    st.divider()

    render_configuration_settings_from_json(settings)
    st.divider()

    render_env_snapshot_from_json(env, metadata)
    st.divider()
