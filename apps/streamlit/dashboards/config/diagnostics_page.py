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

    diagnostics, admin_cfg = fetch_ready_config_state()

    # --------------------------------------------------------------------------
    # Connectivity / availability banner
    # --------------------------------------------------------------------------
    if diagnostics is None:
        banner_connectivity_error()
        return

    status_code = diagnostics.pop("_http_status_code", 200)

    if not isinstance(diagnostics.get("is_consumable"), bool):
        banner_protocol_error(diagnostics=diagnostics)
        return

    if not diagnostics.get("is_consumable", False):
        banner_non_ready_state(
            status_code=status_code,
            diagnostics=diagnostics,
        )
        return

    ready_state = diagnostics.get("ready_state") or {}

    env = ready_state.get("env") or {}
    settings = ready_state.get("settings") or {}
    metadata = ready_state.get("metadata") or {}

    # --------------------------------------------------------------------------
    # Header: Config FSM
    # --------------------------------------------------------------------------
    render_fsm_status_card(diagnostics=diagnostics)
    st.divider()

    # --------------------------------------------------------------------------
    # Tabs: structured deep-dive
    # --------------------------------------------------------------------------
    overview_tab, config_tab, env_tab, raw_tab = st.tabs(
        ["Overview", "Configuration", "Environment & Metadata", "Raw JSON"]
    )

    with overview_tab:
        render_runtime_overview(diagnostics)

    with config_tab:
        render_configuration_settings(settings)

    with env_tab:
        render_environment(env, metadata)

    with raw_tab:
        st.subheader("Raw `/config-diagnostics` snapshot")
        st.json(diagnostics)
