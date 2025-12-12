from collections.abc import Mapping
from datetime import datetime
from typing import Any

import streamlit as st

HEALTHY_ICON = """
<svg aria-labelledby="healthy-desc"
     role="img"
     width="24"
     height="24"
     viewBox="0 0 32 32"
     xmlns="http://www.w3.org/2000/svg">
  <desc id="healthy-desc">Healthy status indicator</desc>
  <circle cx="16" cy="16" r="16" fill="#55A362"></circle>
  <path d="M12.799 20.83l-.005-.003L9.94 17.97a1.5 1.5 0 1 1 2.121-2.12l1.8 1.798 6.209-6.21a1.5 1.5 0 1 1 2.12 2.122l-7.264 7.264-.005.006a1.5 1.5 0 0 1-2.121 0z"
        fill="#FFFFFF" />
</svg>
"""

UNHEALTHY_ICON = """
<svg aria-labelledby="unhealthy-desc"
     role="img"
     width="24"
     height="24"
     viewBox="0 0 16 16"
     xmlns="http://www.w3.org/2000/svg">
  <desc id="unhealthy-desc">Unhealthy status indicator</desc>
  <circle cx="8" cy="8" r="8" fill="#CD4A45"></circle>
  <path d="M10.984 5.004a.9.9 0 0 1 0 1.272L9.27 7.99l1.74 1.741a.9.9 0 1 1-1.272 1.273l-1.74-1.741-1.742 1.74a.9.9 0 1 1-1.272-1.272l1.74-1.74-1.713-1.714a.9.9 0 0 1 1.273-1.273l1.713 1.713 1.714-1.713a.9.9 0 0 1 1.273 0z"
        fill="#FFFFFF" />
</svg>
"""


def _format_timestamp(ts: str | None) -> str:
    if not ts:
        return "n/a"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return ts  # fallback


def _all_systems_ok(snapshot: Mapping[str, Any]) -> bool:
    """True if all monitored subsystems are UP."""
    return all(
        [
            snapshot["pipeline_up"],
            snapshot["logging_ok"],
            snapshot["logging_sink_up"],
            snapshot["tracing_ok"],
            snapshot["tracing_up"],
            snapshot["metrics_http_ok"],
        ]
    )


def _badge(ok: bool) -> str:
    return HEALTHY_ICON if ok else UNHEALTHY_ICON


def render_overall_status(snapshot: Mapping[str, Any]) -> None:
    """Render a centered overall system health indicator."""
    all_ok = _all_systems_ok(snapshot)

    color = "#107C10" if all_ok else "#C8C8C8"

    container_html = f"""
<div style="
    display: flex;
    flex-direction: column;
    align-items: center;
    margin: 2rem 0 2.5rem 0;
">

<svg aria-hidden="true" height="80" width="80"
     viewBox="0 0 80 80"
     xmlns="http://www.w3.org/2000/svg">
    <path fill="{color}" d="M17.5 15C16.8229 15 16.237 14.7526 15.7422 14.2578C15.2474 13.763 15 13.1771 15 12.5C15 11.8229 15.2474 11.237 15.7422 10.7422C16.237 10.2474 16.8229 10 17.5 10H27.5C28.1771 10 28.763 10.2474 29.2578 10.7422C29.7526 11.237 30 11.8229 30 12.5C30 13.1771 29.7526 13.763 29.2578 14.2578C28.763 14.7526 28.1771 15 27.5 15H17.5ZM52.5 15C51.8229 15 51.237 14.7526 50.7422 14.2578C50.2474 13.763 50 13.1771 50 12.5C50 11.8229 50.2474 11.237 50.7422 10.7422C51.237 10.2474 51.8229 10 52.5 10H62.5C63.1771 10 63.763 10.2474 64.2578 10.7422C64.7526 11.237 65 11.8229 65 12.5C65 13.1771 64.7526 13.763 64.2578 14.2578C63.763 14.7526 63.1771 15 62.5 15H52.5ZM7.5 25C6.82292 25 6.23698 24.7526 5.74219 24.2578C5.2474 23.763 5 23.1771 5 22.5C5 21.8229 5.2474 21.237 5.74219 20.7422C6.23698 20.2474 6.82292 20 7.5 20H35C35.6771 20 36.263 20.2474 36.7578 20.7422C37.2526 21.237 37.5 21.8229 37.5 22.5C37.5 23.1771 37.2526 23.763 36.7578 24.2578C36.263 24.7526 35.6771 25 35 25H7.5ZM45 25C44.3229 25 43.737 24.7526 43.2422 24.2578C42.7474 23.763 42.5 23.1771 42.5 22.5C42.5 21.8229 42.7474 21.237 43.2422 20.7422C43.737 20.2474 44.3229 20 45 20H72.5C73.1771 20 73.763 20.2474 74.2578 20.7422C74.7526 21.237 75 21.8229 75 22.5C75 23.1771 74.7526 23.763 74.2578 24.2578C73.763 24.7526 73.1771 25 72.5 25H45ZM77.5 30C78.1771 30 78.763 30.2474 79.2578 30.7422C79.7526 31.237 80 31.8229 80 32.5C80 33.1771 79.7526 33.763 79.2578 34.2578C78.763 34.7526 78.1771 35 77.5 35H2.5C1.82292 35 1.23698 34.7526 0.742188 34.2578C0.247396 33.763 0 33.1771 0 32.5C0 31.8229 0.247396 31.237 0.742188 30.7422C1.23698 30.2474 1.82292 30 2.5 30H77.5ZM72.5 40C73.1771 40 73.763 40.2474 74.2578 40.7422C74.7526 41.237 75 41.8229 75 42.5C75 43.1771 74.7526 43.763 74.2578 44.2578C73.763 44.7526 73.1771 45 72.5 45H7.5C6.82292 45 6.23698 44.7526 5.74219 44.2578C5.2474 43.763 5 43.1771 5 42.5C5 41.8229 5.2474 41.237 5.74219 40.7422C6.23698 40.2474 6.82292 40 7.5 40H72.5ZM62.5 50C63.1771 50 63.763 50.2474 64.2578 50.7422C64.7526 51.237 65 51.8229 65 52.5C65 53.1771 64.7526 53.763 64.2578 54.2578C63.763 54.7526 63.1771 55 62.5 55H17.5C16.8229 55 16.237 54.7526 15.7422 54.2578C15.2474 53.763 15 53.1771 15 52.5C15 51.8229 15.2474 51.237 15.7422 50.7422C16.237 50.2474 16.8229 50 17.5 50H62.5ZM52.5 60C53.1771 60 53.763 60.2474 54.2578 60.7422C54.7526 61.237 55 61.8229 55 62.5C55 63.1771 54.7526 63.763 54.2578 64.2578C53.763 64.7526 53.1771 65 52.5 65H27.5C26.8229 65 26.237 64.7526 25.7422 64.2578C25.2474 63.763 25 63.1771 25 62.5C25 61.8229 25.2474 61.237 25.7422 60.7422C26.237 60.2474 26.8229 60 27.5 60H52.5ZM42.5 70C43.1771 70 43.763 70.2474 44.2578 70.7422C44.7526 71.237 45 71.8229 45 72.5C45 73.1771 44.7526 73.763 44.2578 74.2578C43.763 74.7526 43.1771 75 42.5 75H37.5C36.8229 75 36.237 74.7526 35.7422 74.2578C35.2474 73.763 35 73.1771 35 72.5C35 71.8229 35.2474 71.237 35.7422 70.7422C36.237 70.2474 36.8229 70 37.5 70H42.5Z"/>
</svg>

<div style="
    text-align:center;
    font-size:1.6rem;
    font-weight:600;
">
    {"Everything is looking good" if all_ok else "Some systems require attention"}
</div>
</div>
    """

    st.markdown(container_html, unsafe_allow_html=True)


def render_header(snapshot: Mapping[str, Any]) -> None:
    st.write(f"**run_id:** `{snapshot['run_id']}`")
    st.write(f"**correlation_id:** `{snapshot['correlation_id']}`")

    st.divider()


def render_health_matrix(snapshot: Mapping[str, Any]) -> None:
    render_overall_status(snapshot)

    rows = [
        ("Pipeline", _badge(snapshot["pipeline_up"]), ""),
        (
            "Logging",
            _badge(snapshot["logging_ok"]),
            f"{_badge(snapshot['logging_sink_up'])} Sink",
        ),
        (
            "Tracing",
            _badge(snapshot["tracing_ok"]),
            f"{_badge(snapshot['tracing_up'])} Reachability",
        ),
        ("Metrics", _badge(snapshot["metrics_http_ok"]), ""),
    ]

    table_css = """
<style>
table {
margin: 0 !important;
}

.health-table {
width: 100%;
border-collapse: collapse;
font-size: 1.05rem;
border: 1px solid #ddd;
}

.health-table th,
.health-table td {
padding: 20px 0;
line-height: 15px;
border-right: 0;
border-left: 0;
}

.health-table th {
text-align: center;
font-weight: 400;
border-bottom: 1px solid #ddd;
}

.health-table td {
border-bottom: 1px solid #eee;
vertical-align: middle;
}

.health-table td:not(:first-child) {
text-align: center;
}

.health-table td:first-child {
padding-left: 20px;
}

.health-table svg {
vertical-align: middle;
}

.legend-container {
background-color: rgba(248, 248, 248, 1);
padding: 20px 16px;
border-top: 1px solid;
border-top-color: rgba(218, 218, 218, 1);
font-size: 0.95rem;
display: flex;
justify-content: center;
align-items: center;
gap: 30px;
}

.legend-item {
display: inline-flex;
align-items: center;
}

.legend-item svg {
margin-right: 6px;
width: 16px;
height: 16px;
}
</style>
    """

    table_html = """
<table class="health-table">
<tr>
<th>Subsystem</th>
<th>Status</th>
<th>Details</th>
</tr>
    """

    for subsystem, status_icon, details in rows:
        table_html += f"""
<tr>
<td>{subsystem}</td>
<td>{status_icon}</td>
<td>{details}</td>
</tr>
        """

    table_html += "</table>"

    legend_html = f"""
<div class="legend-container">
<div class="legend-item">{HEALTHY_ICON} Healthy</div>
<div class="legend-item">{UNHEALTHY_ICON} Unhealthy</div>
</div>
    """

    st.markdown(table_css + table_html + legend_html, unsafe_allow_html=True)
    st.divider()


def render_diagnostics_section(snapshot: Mapping[str, Any]) -> None:
    st.header("Bootstrap Diagnostics (Init Latencies & Failures)")
    diagnostics = snapshot.get("diagnostics", {})

    if "error" in diagnostics:
        st.error(f"Diagnostics unavailable: {diagnostics['error']}")
        return

    latencies = diagnostics.get("latencies", {})
    failures = diagnostics.get("failures", [])

    # Latencies
    with st.expander("Initialization Latencies (seconds)", expanded=True):
        if latencies:
            st.json(latencies)
        else:
            st.write("_No latencies recorded._")

    # Failures
    with st.expander("Initialization Failures"):
        if failures:
            st.error("Some subsystems failed during initialization:")
            st.json(failures)
        else:
            st.success("No initialization failures recorded.")

    st.divider()


def render_raw_json(snapshot: Mapping[str, Any]) -> None:
    with st.expander("Raw JSON Snapshot", expanded=False):
        st.json(snapshot)
