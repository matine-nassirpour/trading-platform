from __future__ import annotations

import streamlit as st

from apps.streamlit.dashboards.observability.diagnostics_service import (
    fetch_observability_diagnostics,
)
from apps.streamlit.dashboards.observability.diagnostics_view import (
    render_diagnostics_section,
    render_health_matrix,
    render_raw_json,
)


def render_observability_dashboard() -> None:
    st.title("🧭 Observability Dashboard")

    snapshot, admin_cfg = fetch_observability_diagnostics()

    if snapshot is None:
        st.error("Observability diagnostics unavailable.")
        st.info(f"Admin HTTP base URL: {admin_cfg.base_url!r}")
        return

    if snapshot.get("_http_status_code") != 200:
        st.error(
            f"Observability endpoint returned HTTP {snapshot['_http_status_code']}."
        )
        return

    render_health_matrix(snapshot)
    render_diagnostics_section(snapshot)
    render_raw_json(snapshot)
