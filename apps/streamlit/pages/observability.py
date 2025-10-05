import json
import logging
import os
import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
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

# ──────────────────────────────────────────────────────────────────────────────
# Constants & Types
# ──────────────────────────────────────────────────────────────────────────────

PAGE_TITLE = "Observability"

LogRenderMode = Literal["code", "json"]
TZMode = Literal["utc", "local"]

LEVEL_EMOJI: Mapping[str, str] = {
    "DEBUG": "🐛",
    "INFO": "ℹ️",
    "WARNING": "⚠️",
    "ERROR": "❌",
    "CRITICAL": "🛑",
}

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PageConfig:
    log_dir: Path | None
    log_renderer: LogRenderMode
    log_expanded: bool
    log_chunk_bytes: int
    log_tail_max_lines: int
    log_glob: str
    log_tz_mode: TZMode

    @staticmethod
    def from_env(env: Mapping[str, str]) -> "PageConfig":
        def _bool(var: str, default: bool = False) -> bool:
            v = env.get(var, str(int(default))).strip().lower()
            return v in {"1", "true", "yes", "on"}

        def _int(var: str, default: int) -> int:
            try:
                return int(env.get(var, str(default)))
            except (TypeError, ValueError):
                return default

        log_dir_env = env.get("QUANTUM_LOG_DIR")
        log_dir = Path(log_dir_env) if log_dir_env else None

        renderer = env.get("STREAMLIT_LOG_RENDERER", "code").strip().lower()
        log_renderer: LogRenderMode = "json" if renderer == "json" else "code"

        tz = env.get("STREAMLIT_LOG_TZ", "utc").strip().lower()
        log_tz_mode: TZMode = "local" if tz == "local" else "utc"

        return PageConfig(
            log_dir=log_dir,
            log_renderer=log_renderer,
            log_expanded=_bool("STREAMLIT_LOG_EXPANDED", False),
            log_chunk_bytes=_int("STREAMLIT_LOG_CHUNK_BYTES", 256_000),
            log_tail_max_lines=_int("STREAMLIT_LOG_TAIL_MAX_LINES", 100),
            log_glob=env.get("STREAMLIT_LOG_GLOB", "events-*.jsonl"),
            log_tz_mode=log_tz_mode,
        )


CFG = PageConfig.from_env(os.environ)

# ──────────────────────────────────────────────────────────────────────────────
# Streamlit page bootstrap
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(page_title=PAGE_TITLE, layout="wide")
st.title("🔭 Observability")

# Reusable loggers / tracers
logger = logging.getLogger("quantum.ui.demo")
tracer = trace.get_tracer("quantum.ui.demo")

# ──────────────────────────────────────────────────────────────────────────────
# Prometheus access helpers
# NOTE: prometheus_client does not provide a public in-process read API.
# We encapsulate internal usage (_collector_to_names) with safeguards.
# ──────────────────────────────────────────────────────────────────────────────


def _collect_metric_by_name(name: str):
    mapping = getattr(REGISTRY, "_collector_to_names", None)
    if mapping is None:
        return None

    try:
        items = (
            mapping.items()
        )  # may raise AttributeError if the object is not dict-like
    except AttributeError:
        return None

    for collector, names in items:
        if name not in names:
            continue

        try:
            for metric in collector.collect():
                if getattr(metric, "name", None) == name:
                    return metric
        except (RuntimeError, TypeError, ValueError) as exc:
            logging.getLogger(__name__).debug(
                "Prometheus collector %r collect() failed: %s", collector, exc
            )
            # We continue: a faulty collector must not block the page
            continue

    return None


def _gauge_value(name: str) -> float | None:
    m = _collect_metric_by_name(name)
    if not m:
        return None
    for s in m.samples:
        if s.name == name and not s.labels:
            try:
                return float(s.value)
            except (TypeError, ValueError):
                return None
    # Fallback: premier sample
    try:
        return float(m.samples[0].value) if m.samples else None
    except (TypeError, ValueError):
        return None


def _counter_value(name: str) -> float | None:
    # Same reading as client-side gauge; server-side Prom prometheus distinguishes
    return _gauge_value(name)


def _histogram_quantiles(
    metric_name_prefix: str, quantiles: Iterable[float] = (0.5, 0.95, 0.99)
) -> dict[str, float | None]:
    """
    Approximates the quantiles of a Prometheus histogram from the cumulative buckets.
    Aggregates across all labels if present.
    """
    m = _collect_metric_by_name(metric_name_prefix + "_bucket")
    quantile_keys = [f"p{int(q * 100)}" for q in quantiles]
    if not m:
        return {k: None for k in quantile_keys}

    # Cumulative aggregation by upper bound
    buckets: dict[float, float] = {}
    for s in m.samples:
        if not s.name.endswith("_bucket"):
            continue
        le = s.labels.get("le") if s.labels else None
        if le is None:
            continue
        try:
            bound = float("inf") if le == "+Inf" else float(le)
            buckets[bound] = buckets.get(bound, 0.0) + float(s.value)
        except (TypeError, ValueError):
            continue

    # total_count via *_count if available, otherwise last terminal
    total_count = 0.0
    m_count = _collect_metric_by_name(metric_name_prefix + "_count")
    if m_count:
        for s in m_count.samples:
            if s.name.endswith("_count"):
                try:
                    total_count = max(total_count, float(s.value))
                except (TypeError, ValueError):
                    pass

    if not buckets:
        return {k: None for k in quantile_keys}

    sorted_bounds = sorted(buckets.items(), key=lambda kv: kv[0])

    def _q(q: float) -> float | None:
        total = total_count or sorted_bounds[-1][1]
        if total <= 0:
            return None

        rank = q * total
        prev_bound = 0.0
        prev_count = 0.0

        for upper_bound, cum in sorted_bounds:
            if rank <= cum:
                in_bucket = cum - prev_count
                if in_bucket <= 0:
                    return upper_bound
                if upper_bound == float("inf"):
                    return prev_bound
                frac = (rank - prev_count) / max(in_bucket, 1e-9)
                return prev_bound + frac * (upper_bound - prev_bound)
            prev_bound, prev_count = upper_bound, cum
        return None

    return {f"p{int(q * 100)}": _q(q) for q in quantiles}


# ──────────────────────────────────────────────────────────────────────────────
# Log reading helpers
# ──────────────────────────────────────────────────────────────────────────────


def _tail_jsonl_complete_lines(
    path: Path, *, chunk_bytes: int, encoding: str = "utf-8"
) -> list[str]:
    """
    Reads the end of a JSONL file, preserving only complete lines.
    Robust to rotations/permissions/encoding.
    """
    try:
        with open(path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            file_end = fh.tell()
            start_offset = max(0, file_end - chunk_bytes)
            fh.seek(start_offset)
            buf = fh.read().decode(encoding, "replace")

        if start_offset > 0:
            buf = buf.split("\n", 1)[-1]  # drop 1st line potentially truncated

        buf = buf.replace("\r\n", "\n")
        raw_lines = buf.split("\n")

        if raw_lines and buf and not buf.endswith("\n"):
            raw_lines = raw_lines[:-1]  # drop last incomplete line

        return [line for line in raw_lines if line.strip()]
    except (OSError, UnicodeDecodeError):
        return []


def _shorten(s: str, max_len: int = 80) -> str:
    s = s.replace("\n", " ").strip()
    return (s[: max_len - 1] + "…") if len(s) > max_len else s


def _fmt_dt(obj: Mapping[str, object], *, tz_mode: TZMode) -> str:
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


def _expander_title_from_obj(obj: Mapping[str, object], *, tz_mode: TZMode) -> str:
    lvl = str(obj.get("level", "INFO")).upper()
    emoji = LEVEL_EMOJI.get(lvl, "•")
    logger_name = str(obj.get("logger") or obj.get("service_name") or "log")
    dt_str = _fmt_dt(obj, tz_mode=tz_mode)
    return f"{emoji} {logger_name} | {dt_str}"


def _render_log(
    line: str, *, render_mode: LogRenderMode, default_expanded: bool, tz_mode: TZMode
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
    files = sorted(
        base_dir.rglob(pattern),
        key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
        reverse=True,
    )
    lines: list[str] = []
    for fp in files[:max_files]:
        lines.extend(_tail_jsonl_complete_lines(fp, chunk_bytes=chunk_bytes))
    return lines


# ──────────────────────────────────────────────────────────────────────────────
# UI sections
# ──────────────────────────────────────────────────────────────────────────────


def render_kpis() -> None:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        v = _gauge_value("quantum_pipeline_up")
        st.metric(
            "Pipeline up", "✅" if v == 1 else "❌", help="End-to-end bootstrap OK"
        )
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


def render_logging_counters() -> None:
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


def render_ui_latency_histograms() -> None:
    q_ui_action = _histogram_quantiles("quantum_ui_action_latency_ms")
    q_ui_render = _histogram_quantiles("quantum_ui_page_render_ms")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("UI Action Latency (ms)")
        st.write(
            {
                k: (round(v, 2) if v is not None else None)
                for k, v in q_ui_action.items()
            }
        )
    with c2:
        st.subheader("UI Page Render (ms)")
        st.write(
            {
                k: (round(v, 2) if v is not None else None)
                for k, v in q_ui_render.items()
            }
        )
    st.divider()


def render_mt5_section() -> None:
    cols = st.columns(4)
    with cols[0]:
        hb = _gauge_value("quantum_mt5_terminal_up")
        st.metric("MT5 Terminal", "✅" if hb == 1 else ("❌" if hb == 0 else "—"))
    with cols[1]:
        st.metric(
            "Positions open", int(_gauge_value("quantum_mt5_positions_open") or 0)
        )
    with cols[2]:
        st.metric(
            "Order rejects", int(_counter_value("quantum_mt5_order_reject_total") or 0)
        )
    with cols[3]:
        st.metric("Requotes", int(_counter_value("quantum_mt5_requotes_total") or 0))
    st.divider()


def render_log_tail(cfg: PageConfig) -> None:
    st.subheader("Recent logs (JSONL tail)")
    if not cfg.log_dir:
        st.info(
            "QUANTUM_LOG_DIR is not set. Enable partitioned file logging to see tail."
        )
        return

    base = cfg.log_dir
    if not base.exists():
        st.warning(f"Log directory does not exist: {base}")
        return

    lines = _read_recent_jsonl_lines(
        base, cfg.log_glob, chunk_bytes=cfg.log_chunk_bytes, max_files=2
    )

    if not lines:
        st.write("No JSONL files yet.")
        return

    for ln in lines[-cfg.log_tail_max_lines :]:
        _render_log(
            ln,
            render_mode=cfg.log_renderer,
            default_expanded=cfg.log_expanded,
            tz_mode=cfg.log_tz_mode,
        )


def render_actions() -> None:
    st.divider()
    st.subheader("Actions")
    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        if st.button("Emit INFO log"):
            # INFO can be sampled -> additional WARNING for visibility
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

    with col_b:
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

    with col_c:
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

    with col_d:
        if st.button("Burst (rollover)"):
            # Generate multiple lines to trigger rotation if QUANTUM_LOG_MAX_BYTES is low
            payload = "X" * 512
            cid = new_correlation_id()
            with correlation_context(cid):
                for i in range(60):
                    logger.warning("burst %s %s", i, payload)
            st.success("Burst emitted ✔ (look at File rotations)")

    st.caption(
        "Tip: use the 'R' key or the ↻ icon to rerun; or set Streamlit auto-refresh."
    )


# ──────────────────────────────────────────────────────────────────────────────
# Page layout
# ──────────────────────────────────────────────────────────────────────────────


render_kpis()
render_logging_counters()
render_ui_latency_histograms()
render_mt5_section()
render_log_tail(CFG)
render_actions()
