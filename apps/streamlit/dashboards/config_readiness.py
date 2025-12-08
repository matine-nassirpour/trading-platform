import os
import platform
import socket

import requests
import streamlit as st

from apps.streamlit.config_runtime_client import AdminHTTPConfig, get_admin_http_config


def fetch_ready_config_state() -> tuple[dict | None, AdminHTTPConfig]:
    """
    Passive read-only retrieval of the Runtime READY state.

    Returns:
        (payload_or_none, admin_http_config)
    """
    admin_cfg = get_admin_http_config()

    if not admin_cfg.enabled or not admin_cfg.base_url:
        # Admin HTTP not reachable (runtime down, disabled, or misconfigured)
        return None, admin_cfg

    # Prefer the fully-qualified endpoint URL if provided by the Runtime,
    # otherwise fall back to base_url + /config-readiness for backward compatibility.
    url = (
        admin_cfg.endpoints.get("config_readiness")
        or f"{admin_cfg.base_url}/config-readiness"
    )

    try:
        r = requests.get(url, timeout=1)
        data = r.json()
        data["_http_status_code"] = r.status_code
        return data, admin_cfg
    except Exception:
        return None, admin_cfg


def fetch_config_diagnostics(admin_cfg: AdminHTTPConfig) -> dict | None:
    if not admin_cfg.enabled or not admin_cfg.base_url:
        return None

    url = (
        admin_cfg.endpoints.get("config_diagnostics")
        or f"{admin_cfg.base_url}/config-diagnostics"
    )

    try:
        r = requests.get(url, timeout=1)
        return r.json()
    except Exception:
        return None


def fetch_full_config_diagnostics(admin_cfg: AdminHTTPConfig) -> dict | None:
    if not admin_cfg.enabled or not admin_cfg.base_url:
        return None

    url = (
        admin_cfg.endpoints.get("config_diagnostics_full")
        or f"{admin_cfg.base_url}/config-diagnostics-full"
    )

    try:
        r = requests.get(url, timeout=2)
        return r.json()
    except Exception:
        return None


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Sections                                                                   │
# ╰────────────────────────────────────────────────────────────────────────────╯
def render_fsm_status(
    *, fsm_version: int, status: str, fingerprint: str, timestamp: str
):
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
    st.markdown(f"FSM Version: {fsm_version}")

    st.markdown("### 🔐 Fingerprint Canonical (SHA-256)")
    st.code(fingerprint, language="text")

    st.write(f"System clock: {timestamp}")


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


def render_config_state_diagnostics(diagnostics: dict):
    st.subheader("🛠️ Config State Diagnostics")

    with st.expander("Process Information"):
        st.json(
            {
                "pid_current": diagnostics.get("pid_current"),
                "pid_recorded": diagnostics.get("pid_recorded"),
                "fork_detected": diagnostics.get("fork_detected"),
            }
        )

    with st.expander("Configuration Parameters"):
        st.json(
            {
                "base_dir": diagnostics.get("base_dir"),
                "env_file": diagnostics.get("env_file"),
                "root_param": diagnostics.get("root_param"),
                "env_file_param": diagnostics.get("env_file_param"),
            }
        )

    with st.expander("Cache Status"):
        st.json(
            {
                "cache_size": diagnostics.get("cache_size"),
                "cache_matches_params": diagnostics.get("cache_matches_params"),
                "has_valid_cache": diagnostics.get("has_valid_cache"),
                "reload_count": diagnostics.get("reload_count"),
            }
        )

    with st.expander("Lock Information"):
        st.json(diagnostics.get("lock_info"))


def render_full_config_diagnostics(diag: dict):
    st.header("🧬 Full Configuration Diagnostics")

    with st.expander("📌 Readiness Snapshot"):
        st.json(diag.get("readiness", {}))

    with st.expander("🧱 ConfigState Snapshot"):
        st.json(diag.get("config_state", {}))

    with st.expander("📚 Environment Resolution"):
        st.json(diag.get("env_resolution", {}))

    with st.expander("📄 Environment Loading"):
        st.json(diag.get("env_loading", {}))

    with st.expander("🗺️ Model Routing"):
        st.json(diag.get("routing", {}))

    with st.expander("⚙️ Final Validated Settings"):
        st.json(diag.get("final_settings", {}))


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Main Page Renderer                                                         │
# ╰────────────────────────────────────────────────────────────────────────────╯
def render_page() -> None:
    ready_config_state, admin_cfg = fetch_ready_config_state()

    if ready_config_state is None:
        if not admin_cfg.enabled:
            st.info(
                "ℹ️ Admin HTTP endpoint is not available.\n\n"
                "The Runtime may be down, unreachable from this environment, "
                "or the admin HTTP control-plane may be disabled."
            )
            return

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

    env = ready_state.get("env", {})
    settings = ready_state.get("settings", {})
    metadata = ready_state.get("metadata", {})

    st.title("🔍 Quantum Observability — Core Dashboard")
    st.write("Realtime supervision of the Quantum Runtime configuration.")
    st.divider()

    render_fsm_status(
        fsm_version=ready_config_state.get("schema_version"),
        status=ready_state.get("status"),
        fingerprint=ready_config_state.get("fingerprint"),
        timestamp=ready_config_state.get("timestamp_utc"),
    )
    st.divider()

    # Runtime overview
    render_runtime_overview_from_json(ready_config_state)
    st.divider()

    render_configuration_settings_from_json(settings)
    st.divider()

    render_env_snapshot_from_json(env, metadata)
    st.divider()

    diagnostics = fetch_config_diagnostics(admin_cfg)
    if diagnostics is not None:
        render_config_state_diagnostics(diagnostics)
        st.divider()
    else:
        st.warning("Unable to fetch Config Diagnostics.")
        st.divider()

    full_diag = fetch_full_config_diagnostics(admin_cfg)
    if full_diag is not None:
        render_full_config_diagnostics(full_diag)
        st.divider()
    else:
        st.warning("Unable to fetch full configuration diagnostics.")
        st.divider()
