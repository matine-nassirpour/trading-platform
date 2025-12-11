import os
import platform
import socket
import textwrap

from collections.abc import Mapping
from datetime import datetime
from typing import Any

import streamlit as st


def _format_timestamp(ts: str | None) -> str:
    if not ts:
        return "n/a"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return ts  # fallback


def render_fsm_status_card(
    *, ready_config_state: Mapping[str, Any], ready_state: Mapping[str, Any]
) -> None:
    status = (ready_state.get("status") or "UNKNOWN").upper()
    fingerprint = ready_config_state.get("fingerprint", "n/a")
    fsm_version = ready_config_state.get("schema_version", "n/a")
    timestamp = ready_config_state.get("timestamp_utc", "n/a")
    formated_timestamp = _format_timestamp(timestamp)

    colors = {
        "READY": ("#0fa958", "white"),
        "ERROR": ("#c2392d", "white"),
    }
    bg_color, text_color = colors.get(status, ("orange", "black"))

    summary_messages = {
        "READY": "The runtime configuration is valid, healthy and operational.",
        "ERROR": "The runtime is NOT ready. Manual intervention is required.",
    }
    summary = summary_messages.get(status, "UNKNOWN")

    st.markdown(
        f"""
        <div style="
            padding: 1.5rem;
            border-radius: 0.8rem;
            background-color: {bg_color};
            color: {text_color};
            margin-bottom: 1.5rem;
        ">
            <h2 style="margin: 0; padding: 0;">FSM STATUS: {status}</h2>
            <p style="margin-top:0.5rem; margin-bottom:0; font-size:1.1rem;">{summary}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="FSM Schema Version", value=str(fsm_version))
    with col2:
        st.metric(
            label="Fingerprint (SHA-256, truncated)", value=fingerprint[:19] + "…"
        )
    with col3:
        st.metric(label="Timestamp (UTC)", value=formated_timestamp)

    with st.expander("Full fingerprint (SHA-256)"):
        st.code(fingerprint, language="text")


def render_runtime_overview(ready_json: Mapping[str, Any]) -> None:
    st.subheader("🧩 Runtime Overview")

    settings = ready_json.get("ready_state", {}).get("settings", {})
    core = settings.get("core", {})

    identity = {
        "service_name": core.get("quantum_app_name"),
        "service_version": core.get("quantum_app_version"),
        "service_namespace": core.get("quantum_ns"),
        "environment": core.get("quantum_env"),
        "instance_id": core.get("quantum_instance_id", "unknown"),
    }

    system = {
        "hostname": socket.gethostname(),
        "os": platform.platform(),
        "cpu_count": os.cpu_count(),
    }

    snapshot = ready_json.get("loader_snapshot", {})

    cache_health = {
        "cache_matches_params": ready_json.get("cache_matches_params"),
        "has_valid_cache": ready_json.get("has_valid_cache"),
    }

    with st.expander("Application Identity", expanded=True):
        st.json(identity)

    with st.expander("System Identity", expanded=True):
        st.json(system)

    with st.expander(
        "Configuration Loader Snapshot (Process-Local State)", expanded=True
    ):
        st.json(snapshot)

    with st.expander("Configuration Cache Integrity", expanded=True):
        st.json(cache_health)

    with st.expander("Reserved Environment Keys (OS-Controlled)", expanded=True):
        st.json(ready_json.get("reserved_keys"))


def render_configuration_settings(settings: Mapping[str, Any]) -> None:
    st.subheader("⚙️ Configuration Settings")

    with st.expander("Core Configuration"):
        st.json(settings.get("core", {}))

    with st.expander("Logging Settings"):
        st.json(settings.get("logging", {}))

    with st.expander("Tracing Settings"):
        st.json(settings.get("tracing", {}))

    with st.expander("MT5 Settings"):
        st.json(settings.get("mt5", {}))


def render_environment(env: Mapping[str, Any], metadata: Mapping[str, Any]) -> None:
    st.subheader("🌍 Effective Environment & Metadata")

    with st.expander("Effective Environment"):
        st.json(env)

    with st.expander("Metadata"):
        st.json(metadata)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Status Banners                                                             │
# ╰────────────────────────────────────────────────────────────────────────────╯
def banner_connectivity_error() -> None:
    """
    Render the banner for the case where the admin HTTP is not reachable
    or the `/config-readiness` endpoint could not be queried successfully.
    """
    st.error(textwrap.dedent("""
            ❌ Admin HTTP control-plane is not available.

            The Quantum Runtime may be:
            - down,
            - unreachable from this environment,
            - or the admin HTTP control-plane may be disabled.

            Please verify:
            - the Runtime process status,
            - network connectivity between Streamlit and the Runtime,
            - admin HTTP configuration (host, port, discovery URL).
            """))


def banner_non_ready_state(*, status_code: int, payload: Mapping[str, Any]) -> None:
    reason = payload.get("reason", "Runtime is not in READY state.")

    st.error(
        f"❌ Quantum Runtime is not READY (HTTP {status_code}).\n\n"
        f"Reason: **{reason}**"
    )
    with st.expander("Raw response payload"):
        st.json(payload)


def banner_protocol_error(*, payload: Mapping[str, Any]) -> None:
    st.error(
        "❌ Protocol error: response payload does not contain the expected `ready_state` key.\n\n"
        "This likely indicates a version mismatch between the Runtime and the dashboard, "
        "or a breaking change in the `/config-readiness` contract."
    )
    with st.expander("Raw response payload"):
        st.json(payload)
