"""
Streamlit Observability Dashboard
────────────────────────────────
Provides a real-time, metrics-driven observability dashboard
for the Quantum runtime environment.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
from opentelemetry import trace

from apps.streamlit.bootstrap import get_runtime_context, init_streamlit

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Constants & Initialization                                                 │
# ╰────────────────────────────────────────────────────────────────────────────╯
PAGE_TITLE = "Observability"
LEVEL_EMOJI: Mapping[str, str] = {
    "DEBUG": "🐛",
    "INFO": "ℹ️",
    "WARN": "⚠️",
    "ERROR": "❌",
    "CRITICAL": "🛑",
}

runtime = get_runtime_context()
cfg_bundle = runtime.config_provider.get_bundle()
log_cfg = cfg_bundle.logging
log_provider = runtime.logging_provider
obs_provider = runtime.observability_provider

init_streamlit()

logger = logging.getLogger("quantum.ui.observability")
tracer = trace.get_tracer("quantum.ui.observability")

st.set_page_config(page_title=PAGE_TITLE, layout="wide")
st.title("🔭 Observability")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ KPI and Metrics Sections                                                   │
# ╰────────────────────────────────────────────────────────────────────────────╯
def render_kpis() -> None:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        v = obs_provider.get_gauge_value("quantum_pipeline_up")
        st.metric(
            "Pipeline up", "✅" if v == 1 else "❌", help="End-to-end bootstrap OK"
        )
    with col2:
        v = obs_provider.get_gauge_value("quantum_tracing_exporter_status")
        st.metric(
            "Tracer exporter",
            "ON" if v == 1 else "OFF",
            help="OTLP/console exporter attached",
        )
    with col3:
        v = obs_provider.get_gauge_value("quantum_logging_sink_up")
        st.metric("Logging sinks", "✅" if v == 1 else "❌")
    with col4:
        v = obs_provider.get_gauge_value("quantum_pipeline_metrics_http_ok")
        st.metric("/metrics HTTP", "ON" if v == 1 else "OFF")
    st.divider()


def render_logging_counters() -> None:
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        v = (
            obs_provider.get_counter_value(
                "quantum_logging_schema_validation_errors_total"
            )
            or 0
        )
        st.metric("Schema validation errors", int(v))
    with cc2:
        v = obs_provider.get_counter_value("quantum_logging_redactions_total") or 0
        st.metric("Redactions", int(v))
    with cc3:
        v = obs_provider.get_counter_value("quantum_logging_file_rotations_total") or 0
        st.metric("File rotations", int(v))
    st.divider()


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Log Rendering                                                              │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _shorten(s: str, max_len: int = 80) -> str:
    s = s.replace("\n", " ").strip()
    return (s[: max_len - 1] + "…") if len(s) > max_len else s


def _fmt_dt(obj: Mapping[str, object], *, tz_mode: str) -> str:
    """
    Returns 'YYYY-MM-DD HH:MM:SS.mmmZ' (UTC) or local (without 'Z').
    """
    # RFC3339 timestamp (with or without Z)
    dt: datetime | None = None
    ts = obj.get("timestamp")
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            dt = None

    # fallback on ts_unix_ms
    if dt is None:
        ms = obj.get("ts_unix_ms")
        if isinstance(ms, (int, float)):
            dt = datetime.fromtimestamp(float(ms) / 1000.0, tz=timezone.utc)
    if dt is None:
        return "—"

    if tz_mode == "local":
        dt = dt.astimezone()
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    else:
        dt = dt.astimezone(timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "Z"


def _expander_title_from_obj(obj: Mapping[str, object], *, tz_mode: str) -> str:
    lvl = str(obj.get("level", "INFO")).upper()
    emoji = LEVEL_EMOJI.get(lvl, "•")
    logger_name = str(obj.get("logger") or obj.get("service_name") or "log")
    dt_str = _fmt_dt(obj, tz_mode=tz_mode)
    return f"{emoji} {logger_name} | {dt_str}"


def _render_log(
    line: str, *, render_mode: str, default_expanded: bool, tz_mode: str
) -> None:
    """Displays a log line in an expander, pretty or raw JSON format."""
    try:
        obj = json.loads(line)
        title = _expander_title_from_obj(obj, tz_mode=tz_mode)
        with st.expander(title, expanded=default_expanded):
            if render_mode == "json":
                st.json(obj)
            else:
                st.code(json.dumps(obj, ensure_ascii=False, indent=2), language="json")
    except (json.JSONDecodeError, TypeError):
        title = f"raw • {_shorten(line)}"
        with st.expander(title, expanded=default_expanded):
            st.code(line, language="json")


@st.cache_data(ttl=1.0, show_spinner=False)
def _read_recent_jsonl_lines(
    base_dir: Path, pattern: str, *, chunk_bytes: int, max_files: int = 2
) -> list[str]:
    return list(
        log_provider.tail_jsonl(
            base_dir, pattern, chunk_bytes=chunk_bytes, max_files=max_files
        )
    )


def render_log_tail() -> None:
    st.subheader("Recent logs (JSONL tail)")
    log_dir = Path(log_cfg.quantum_log_dir) if log_cfg.quantum_log_dir else None
    if not log_dir:
        st.info("QUANTUM_LOG_DIR not set. Enable file logging to view logs.")
        return
    if not log_dir.exists():
        st.warning(f"Log directory does not exist: {log_dir}")
        return

    lines = _read_recent_jsonl_lines(
        log_dir,
        log_cfg.streamlit_log_glob,
        chunk_bytes=log_cfg.streamlit_log_chunk_bytes,
        max_files=2,
    )

    if not lines:
        st.write("No JSONL files yet.")
        return

    for ln in lines[-log_cfg.streamlit_log_tail_max_lines :]:
        _render_log(
            ln,
            render_mode=log_cfg.streamlit_log_renderer,
            default_expanded=log_cfg.streamlit_log_expanded,
            tz_mode=log_cfg.streamlit_log_tz,
        )


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Actions Section                                                            │
# ╰────────────────────────────────────────────────────────────────────────────╯
def render_actions() -> None:
    st.divider()
    st.subheader("Actions")
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if st.button("Emit INFO log"):
            log_provider.emit_info(
                "demo info log",
                action="emit_info",
                secret="fake-secret",  # pragma: allowlist secret
            )
            log_provider.emit_info(
                "demo info log (visible)", action="emit_info_visible"
            )
            st.success("INFO/Warning log emitted ✔")

    with col_b:
        if st.button("Emit span + log"):
            with tracer.start_as_current_span("ui.demo.parent"):
                log_provider.emit_info("log inside parent span", in_span=True)
                with tracer.start_as_current_span("ui.demo.child"):
                    log_provider.emit_info("log inside child span", in_span_child=True)
            st.success("Span(s) + logs emitted ✔")

    with col_c:
        if st.button("Emit audit event"):
            log_provider.emit_event(
                {
                    "event_name": "order_submit_v1",
                    "schema_version": 1,
                    "order_id": "demo-ui-1",
                    "symbol": "EURUSD",
                    "side": "buy",
                    "qty": 0.01,
                    "price": 1.23456,
                    "ts": int(time.time() * 1000),
                }
            )
            st.success("Audit event emitted ✔ (voir dossier _audit)")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Page layout                                                                │
# ╰────────────────────────────────────────────────────────────────────────────╯
def main() -> None:
    render_kpis()
    render_logging_counters()
    render_log_tail()
    render_actions()


if __name__ == "__main__":
    main()
