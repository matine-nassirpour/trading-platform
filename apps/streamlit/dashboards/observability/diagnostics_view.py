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


def render_status_badge(ok: bool) -> str:
    if ok:
        return "🟢 **UP**"
    else:
        return "🔴 **DOWN**"


def render_header(snapshot: Mapping[str, Any]) -> None:
    timestamp = snapshot["timestamp_utc"]
    formated_timestamp = _format_timestamp(timestamp)

    cols = st.columns([1, 2])

    with cols[0]:
        st.metric(
            label="Pipeline",
            value="UP" if snapshot["pipeline_up"] else "DOWN",
        )
        st.metric(
            label="Logging OK",
            value="YES" if snapshot["logging_ok"] else "NO",
        )
        st.metric(
            label="Tracing OK",
            value="YES" if snapshot["tracing_ok"] else "NO",
        )
        st.metric(
            label="Metrics HTTP OK",
            value="YES" if snapshot["metrics_http_ok"] else "NO",
        )

    with cols[1]:
        st.write(f"**Timestamp (UTC):** `{formated_timestamp}`")
        st.write(f"**run_id:** `{snapshot['run_id']}`")
        st.write(f"**correlation_id:** `{snapshot['correlation_id']}`")

    st.markdown("---")


def render_subsystem_status(snapshot: Mapping[str, Any]) -> None:
    st.header("Subsystem Status")

    cols = st.columns(3)

    with cols[0]:
        st.markdown("### Logging")
        st.write(render_status_badge(snapshot["logging_ok"]))
        st.write("**Sink:** " + render_status_badge(snapshot["logging_sink_up"]))

    with cols[1]:
        st.markdown("### Tracing")
        st.write(render_status_badge(snapshot["tracing_ok"]))
        st.write("**Reachability:** " + render_status_badge(snapshot["tracing_up"]))

    with cols[2]:
        st.markdown("### Metrics")
        st.write(render_status_badge(snapshot["metrics_http_ok"]))

    st.markdown("---")


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

    st.markdown("---")


def render_raw_json(snapshot: Mapping[str, Any]) -> None:
    with st.expander("Raw JSON Snapshot", expanded=False):
        st.json(snapshot)
