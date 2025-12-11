from __future__ import annotations

import streamlit as st

from apps.streamlit.dashboards.config.diagnostics_service import (
    fetch_ready_config_state,
)
from apps.streamlit.dashboards.config.diagnostics_view import (
    banner_connectivity_error,
    banner_non_ready_state,
    banner_protocol_error,
    render_configuration_settings,
    render_environment,
    render_fsm_status_card,
    render_runtime_overview,
)


def render_config_dashboard() -> None:
    st.title("🛠️ Configuration Dashboard")

    ready_json, admin_cfg = fetch_ready_config_state()

    # --------------------------------------------------------------------------
    # Connectivity / availability banner
    # --------------------------------------------------------------------------
    if ready_json is None:
        banner_connectivity_error()
        return

    status_code = ready_json.pop("_http_status_code", 200)

    if status_code != 200:
        banner_non_ready_state(status_code=status_code, payload=ready_json)
        return

    ready_state = ready_json.get("ready_state")
    if not isinstance(ready_state, dict):
        banner_protocol_error(payload=ready_json)
        return

    # READY path (canonical structure)
    env = ready_state.get("env") or {}
    settings = ready_state.get("settings") or {}
    metadata = ready_state.get("metadata") or {}

    # --------------------------------------------------------------------------
    # Header: Config FSM
    # --------------------------------------------------------------------------
    render_fsm_status_card(
        ready_config_state=ready_json,
        ready_state=ready_state,
    )
    st.divider()

    # --------------------------------------------------------------------------
    # Tabs: structured deep-dive
    # --------------------------------------------------------------------------
    overview_tab, config_tab, env_tab, raw_tab = st.tabs(
        ["Overview", "Configuration", "Environment & Metadata", "Raw JSON"]
    )

    with overview_tab:
        render_runtime_overview(ready_json)

    with config_tab:
        render_configuration_settings(settings)

    with env_tab:
        render_environment(env, metadata)

    with raw_tab:
        st.subheader("Raw `ready_config_state` payload")
        st.json(ready_json)
