import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import streamlit as st
from opentelemetry import trace
from prometheus_client import REGISTRY

from quantum.infrastructure.observability.logging.event_emitter import emit_event
from quantum.shared.correlation.correlation_id import (
    correlation_context,
    new_correlation_id,
)

PAGE_TITLE = "Observability"
st.set_page_config(page_title=PAGE_TITLE, layout="wide")
st.title("🔭 Observability")


# ------- Helpers to read Prometheus metrics in-process ----------------------
def _collect_metric_by_name(name: str):
    for collector in REGISTRY._collector_to_names:
        names = REGISTRY._collector_to_names[collector]
        if name in names:
            for metric in collector.collect():
                if metric.name == name:
                    return metric
    return None


def _gauge_value(name: str) -> float | None:
    m = _collect_metric_by_name(name)
    if not m:
        return None
    # Expect one sample without labels
    for s in m.samples:
        if s.name == name:
            return float(s.value)
    return None


def _counter_value(name: str) -> float | None:
    return _gauge_value(name)


# ------- Prometheus histogram quantile from buckets -------------------------
def _histogram_quantiles(
    metric_name_prefix: str, quantiles=(0.5, 0.95, 0.99)
) -> dict[str, float | None]:
    m = _collect_metric_by_name(metric_name_prefix + "_bucket")
    if not m:
        return {f"p{int(q*100)}": None for q in quantiles}

    # Aggregate across label sets if present (sum of buckets)
    buckets: dict[float, float] = {}
    total_count = 0.0

    for s in m.samples:
        if not s.name.endswith("_bucket"):
            continue
        le = s.labels.get("le")
        if le is None:
            continue
        try:
            bound = float("inf") if le == "+Inf" else float(le)
        except ValueError:
            continue
        buckets[bound] = buckets.get(bound, 0.0) + float(s.value)

    # read *_count and *_sum if available (for info)
    m_count = _collect_metric_by_name(metric_name_prefix + "_count")
    if m_count:
        for s in m_count.samples:
            if s.name.endswith("_count"):
                total_count += float(s.value)

    m_sum = _collect_metric_by_name(metric_name_prefix + "_sum")
    if m_sum:
        for s in m_sum.samples:
            if s.name.endswith("_sum"):
                _ = float(s.value)

    if not buckets:
        return {f"p{int(q*100)}": None for q in quantiles}

    # Ensure sorted by upper bound
    sorted_bounds = sorted(buckets.items(), key=lambda kv: kv[0])

    def _q(q: float) -> float | None:
        if total_count <= 0:
            # try to infer from the highest bucket
            total = sorted_bounds[-1][1]
        else:
            total = total_count
        if total <= 0:
            return None
        rank = q * total
        prev_bound = 0.0
        prev_count = 0.0
        for bound, cum in sorted_bounds:
            if rank <= cum:
                # linear interpolation inside bucket [prev_bound, bound]
                in_bucket = cum - prev_count
                if in_bucket <= 0:
                    return bound
                frac = (rank - prev_count) / max(in_bucket, 1e-9)
                # handle inf bucket
                if bound == float("inf"):
                    return prev_bound  # can't interpolate; fallback to lower bound
                return prev_bound + frac * (bound - prev_bound)
            prev_bound, prev_count = bound, cum
        return None

    return {f"p{int(q*100)}": _q(q) for q in quantiles}


# ------- KPI Row ------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
with col1:
    v = _gauge_value("quantum_pipeline_up")
    st.metric("Pipeline up", "✅" if v == 1 else "❌", help="End-to-end bootstrap OK")
with col2:
    v = _gauge_value("quantum_tracer_exporter_active")
    st.metric(
        "Tracer exporter",
        "ON" if v == 1 else "OFF",
        help="OTLP/console exporter attached",
    )
with col3:
    v = _gauge_value("quantum_logging_sink_up")
    st.metric("Logging sinks", "✅" if v == 1 else "❌")
with col4:
    v = _gauge_value("quantum_pipeline_metrics_http_ok")
    st.metric("/metrics HTTP", "ON" if v == 1 else "OFF")

st.divider()


# ------- Logging & schema counters ------------------------------------------
cc1, cc2, cc3 = st.columns(3)
with cc1:
    v = _counter_value("quantum_logging_schema_validation_errors_total") or 0
    st.metric("Schema validation errors", int(v))
with cc2:
    v = _counter_value("quantum_logging_redactions_total") or 0
    st.metric("Redactions", int(v))
with cc3:
    v = _counter_value("quantum_logging_file_rotations_total") or 0
    st.metric("File rotations", int(v))

st.divider()


# ------- UI latency histograms (ms) -----------------------------------------
q_ui_action = _histogram_quantiles("quantum_ui_action_latency_ms")
q_ui_render = _histogram_quantiles("quantum_ui_page_render_ms")

c1, c2 = st.columns(2)
with c1:
    st.subheader("UI Action Latency (ms)")
    st.write(
        {k: (round(v, 2) if v is not None else None) for k, v in q_ui_action.items()}
    )
with c2:
    st.subheader("UI Page Render (ms)")
    st.write(
        {k: (round(v, 2) if v is not None else None) for k, v in q_ui_render.items()}
    )

st.divider()


# ------- MT5 (if running) ---------------------------------------------------
mt5_cols = st.columns(4)
with mt5_cols[0]:
    hb = _gauge_value("mt5_terminal_up")
    st.metric("MT5 Terminal", "✅" if hb == 1 else ("❌" if hb == 0 else "—"))
with mt5_cols[1]:
    st.metric("Positions open", int(_gauge_value("mt5_positions_open") or 0))
with mt5_cols[2]:
    st.metric("Order rejects", int(_counter_value("mt5_order_reject_total") or 0))
with mt5_cols[3]:
    st.metric("Requotes", int(_counter_value("mt5_requotes_total") or 0))

st.divider()


# ------- Log tail -----------------------------------------------------------
st.subheader("Recent logs (JSONL tail)")

_LEVEL_EMOJI = {
    "DEBUG": "🐛",
    "INFO": "ℹ️",
    "WARNING": "⚠️",
    "ERROR": "❌",
    "CRITICAL": "🛑",
}


def _tail_jsonl_complete_lines(
    path: Path,
    *,
    chunk_bytes: int = 256_000,
    encoding: str = "utf-8",
) -> list[str]:
    try:
        with open(path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            file_end = fh.tell()
            start_offset = max(0, file_end - chunk_bytes)
            fh.seek(start_offset)
            buf = fh.read().decode(encoding, "replace")

        if start_offset > 0:
            # remove the first partial line if we started mid-file
            buf = buf.split("\n", 1)[-1]

        buf = buf.replace("\r\n", "\n")
        raw_lines: list[str] = buf.split("\n")

        # drop the last potentially incomplete line if file didn't end with '\n'
        if raw_lines and buf and not buf.endswith("\n"):
            raw_lines = raw_lines[:-1]

        # keep only non-empty, trimmed lines
        return [line for line in raw_lines if line.strip()]
    except (OSError, UnicodeDecodeError):
        # file missing/rotated/permission or bad bytes
        return []


def _shorten(s: str, max_len: int = 80) -> str:
    s = s.replace("\n", " ").strip()
    return (s[: max_len - 1] + "…") if len(s) > max_len else s


def _fmt_dt(obj: dict, *, tz_mode: str = "utc") -> str:
    """
    Returns 'YYYY-MM-DD HH:MM:SS.mmmZ' (UTC) or local (without 'Z').
    tz_mode: 'utc' | 'local'
    """
    # 1) timestamp RFC3339 ms
    ts = obj.get("timestamp")
    dt: datetime | None = None
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            dt = None
    # 2) fallback sur ts_unix_ms
    if dt is None:
        ms = obj.get("ts_unix_ms")
        if isinstance(ms, (int, float)):
            dt = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)

    if dt is None:
        return "—"

    if tz_mode == "local":
        dt = dt.astimezone()  # local time zone
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # ex: 2025-10-04 19:18:24.840
    else:
        dt = dt.astimezone(timezone.utc)
        return (
            dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "Z"
        )  # ex: 2025-10-04 17:18:24.840Z


def _expander_title_from_obj(obj: dict) -> str:
    lvl = str(obj.get("level", "INFO")).upper()
    emoji = _LEVEL_EMOJI.get(lvl, "•")
    logger_name = str(obj.get("logger") or obj.get("service_name") or "log")

    tz_mode = os.getenv("STREAMLIT_LOG_TZ", "utc").strip().lower()
    dt_str = _fmt_dt(obj, tz_mode=tz_mode if tz_mode in {"utc", "local"} else "utc")

    return f"{emoji} {logger_name} | {dt_str}"


def _render_log(
    line: str,
    *,
    render_mode: Literal["code", "json"] = "code",
    default_expanded: bool = False,
) -> None:
    """Renders a log in an expander with its own title."""
    try:
        obj = json.loads(line)
        title = _expander_title_from_obj(obj)
        with st.expander(title, expanded=default_expanded):
            if render_mode == "json":
                st.json(obj)
            else:
                st.code(json.dumps(obj, ensure_ascii=False, indent=2), language="json")
    except (json.JSONDecodeError, TypeError):
        # Invalid/incomplete line: togglable + raw rendering
        title = f"raw • {_shorten(line)}"
        with st.expander(title, expanded=default_expanded):
            st.code(line, language="json")


base = os.getenv("QUANTUM_LOG_DIR")
if not base:
    st.info("QUANTUM_LOG_DIR is not set. Enable partitioned file logging to see tail.")
else:
    base_p = Path(base)
    files = sorted(
        base_p.rglob("events-*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not files:
        st.write("No JSONL files yet.")
    else:
        lines: list[str] = []
        for fp in files[:2]:
            lines.extend(_tail_jsonl_complete_lines(fp))

        mode_env = os.getenv("STREAMLIT_LOG_RENDERER", "code").strip().lower()
        render_mode: Literal["code", "json"] = "json" if mode_env == "json" else "code"
        expanded = os.getenv("STREAMLIT_LOG_EXPANDED", "0").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        for ln in lines[-100:]:
            _render_log(ln, render_mode=render_mode, default_expanded=expanded)


# ------- Actions (emit logs / spans / audit) --------------------------------
st.divider()
st.subheader("Actions")

logger = logging.getLogger("quantum.ui.demo")
tracer = trace.get_tracer("quantum.ui.demo")

colA, colB, colC, colD = st.columns(4)

with colA:
    if st.button("Emit INFO log"):
        # NOTE: Depending on .env, the INFO may be sampled;
        # a WARNING is also issued to ensure a visible line.
        cid = new_correlation_id()
        with correlation_context(cid):
            logger.info(
                "demo info log",
                extra={
                    "attrs": {
                        "action": "emit_info",
                        "secret": "fake-secret",  # pragma: allowlist secret
                    }
                },
            )
            logger.warning(
                "demo info log (visible)",
                extra={"attrs": {"action": "emit_info_visible"}},
            )
        st.success("INFO/Warning log emitted ✔")

with colB:
    if st.button("Emit span + log"):
        cid = new_correlation_id()
        with correlation_context(cid):
            with tracer.start_as_current_span("ui.demo.parent"):
                logger.warning(
                    "log inside parent span", extra={"attrs": {"in_span": True}}
                )
                with tracer.start_as_current_span("ui.demo.child"):
                    logger.warning(
                        "log inside child span",
                        extra={"attrs": {"in_span_child": True}},
                    )
        st.success("Span(s) + logs emitted ✔")

with colC:
    if st.button("Emit audit event"):
        cid = new_correlation_id()
        with correlation_context(cid):
            emit_event(
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

with colD:
    if st.button("Burst (rollover)"):
        # Generate multiple lines to trigger rotation if QUANTUM_LOG_MAX_BYTES is low
        payload = "X" * 512
        cid = new_correlation_id()
        with correlation_context(cid):
            for i in range(60):
                logger.warning(f"burst {i} {payload}")
        st.success("Burst emitted ✔ (look at File rotations)")


# Refresh control
st.caption(
    "Tip: use the 'R' key or the ↻ icon to rerun; or set Streamlit auto-refresh."
)
