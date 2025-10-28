import json
import logging
import os
import time
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
from opentelemetry import trace
from prometheus_client import REGISTRY

from apps.streamlit.config_runtime import get_config
from quantum.infrastructure.observability.logging.event_emitter import emit_event
from quantum.infrastructure.observability.tracing.correlation.correlation_id import (
    correlation_context,
    new_correlation_id,
)
from quantum.platform.config.models.logging import LoggingSettings
from quantum.platform.config.runtime.state import CONFIG_STATE

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

# One-time config initialization (cached per Streamlit session)
CFG_BUNDLE = get_config()
LOG_CFG = CFG_BUNDLE.logging

logger = logging.getLogger("quantum.ui.observability")
tracer = trace.get_tracer("quantum.ui.observability")

logging.info("🔭 Observability page initialized via QuantumConfigBundle.")
logging.info("Quantum configuration initialized: %s", CONFIG_STATE.describe())

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Streamlit page Setup                                                       │
# ╰────────────────────────────────────────────────────────────────────────────╯
st.set_page_config(page_title=PAGE_TITLE, layout="wide")
st.title("🔭 Observability")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Prometheus access helpers                                                  │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _iter_metrics():
    """
    Iterates over all metrics exposed by the registry via the public API.
    Gracefully degrades on error (no yield).
    """
    try:
        yield from REGISTRY.collect()
    except Exception as exc:
        logging.getLogger(__name__).debug(f"REGISTRY.collect() failed: {exc}")


def _gauge_value(name: str) -> float | None:
    """
    Returns the value of a Gauge (or Counter) without exact labels.
    Searches for the sample `name{}` among all collectors.
    """
    try:
        for metric in _iter_metrics():
            for s in getattr(metric, "samples", ()):
                if s.name == name and not s.labels:
                    try:
                        return float(s.value)
                    except (TypeError, ValueError):
                        return None
        return None
    except Exception as exc:
        logging.getLogger(__name__).debug("gauge_value(%s) failed: %s", name, exc)
        return None


def _counter_value(name: str) -> float | None:
    return _gauge_value(name)


def _histogram_quantiles(
    metric_name_prefix: str, quantiles: Iterable[float] = (0.5, 0.95, 0.99)
) -> dict[str, float | None]:
    """
    Approximates histogram quantiles from cumulative buckets.

    Aggregates over **all** possible labels: sums all buckets
    `metric_name_prefix_bucket{...}` for a given bound `le`, and uses
    `metric_name_prefix_count` for the total if available.

    API used: REGISTRY.collect() (public).
    """
    try:
        # cumulative buckets across label sets
        buckets: dict[float, float] = {}
        total_count = 0.0

        for metric in _iter_metrics():
            if getattr(metric, "name", None) != metric_name_prefix:
                continue
            for s in getattr(metric, "samples", ()):
                n = s.name
                if not isinstance(n, str):
                    continue
                if n.endswith("_bucket"):
                    le = s.labels.get("le") if s.labels else None  # type: ignore[attr-defined]
                    if le is None:
                        continue
                    try:
                        bound = float("inf") if le == "+Inf" else float(le)
                        buckets[bound] = buckets.get(bound, 0.0) + float(s.value)
                    except (TypeError, ValueError):
                        continue
                elif n.endswith("_count"):
                    try:
                        total_count = max(total_count, float(s.value))
                    except (TypeError, ValueError):
                        pass

        quantile_keys = [f"p{int(q * 100)}" for q in quantiles]

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
    except Exception as exc:
        logging.getLogger(__name__).debug(
            "histogram_quantiles(%s) failed: %s", metric_name_prefix, exc
        )
        return {f"p{int(q * 100)}": None for q in quantiles}


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Log reading helpers                                                        │
# ╰────────────────────────────────────────────────────────────────────────────╯
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
    files = sorted(
        base_dir.rglob(pattern),
        key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
        reverse=True,
    )
    lines: list[str] = []
    for fp in files[:max_files]:
        lines.extend(_tail_jsonl_complete_lines(fp, chunk_bytes=chunk_bytes))
    return lines


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ UI sections                                                                │
# ╰────────────────────────────────────────────────────────────────────────────╯
def render_kpis() -> None:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        v = _gauge_value("quantum_pipeline_up")
        st.metric(
            "Pipeline up", "✅" if v == 1 else "❌", help="End-to-end bootstrap OK"
        )
    with col2:
        v = _gauge_value("quantum_tracing_exporter_status")
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
    q_ui_action_s = _histogram_quantiles("quantum_ui_action_latency_seconds")
    q_ui_render_s = _histogram_quantiles("quantum_ui_page_render_seconds")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("UI Action Latency (seconds)")
        st.write(
            {
                k: (round(v, 2) if v is not None else None)
                for k, v in q_ui_action_s.items()
            }
        )
    with c2:
        st.subheader("UI Page Render (seconds)")
        st.write(
            {
                k: (round(v, 2) if v is not None else None)
                for k, v in q_ui_render_s.items()
            }
        )
    st.divider()


def render_mt5_section() -> None:
    st.subheader("MetaTrader5 Gateway Status")

    cols = st.columns(4)
    with cols[0]:
        hb = _gauge_value("quantum_mt5_terminal_up")
        st.metric("MT5 Terminal", "✅" if hb == 1 else ("❌" if hb == 0 else "—"))
    with cols[1]:
        st.metric(
            "Positions Open", int(_gauge_value("quantum_mt5_positions_open") or 0)
        )
    with cols[2]:
        st.metric(
            "Order Rejects", int(_counter_value("quantum_mt5_order_reject_total") or 0)
        )
    with cols[3]:
        st.metric("Requotes", int(_counter_value("quantum_mt5_requotes_total") or 0))

    # New subsection: Execution Channels
    st.markdown("#### Execution Channel Metrics")
    exec_total = _counter_value("quantum_mt5_exec_channel_total") or 0
    exec_lat_q = _histogram_quantiles("quantum_mt5_exec_channel_latency_ms")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Exec Calls", int(exec_total))
    with col2:
        st.write(
            {k: (round(v, 2) if v is not None else None) for k, v in exec_lat_q.items()}
        )

    st.divider()


def render_log_tail(cfg: LoggingSettings) -> None:
    st.subheader("Recent logs (JSONL tail)")

    log_dir = Path(cfg.quantum_log_dir) if cfg.quantum_log_dir else None
    if not log_dir:
        st.info("QUANTUM_LOG_DIR not set. Enable file logging to view logs.")
        return
    if not log_dir.exists():
        st.warning(f"Log directory does not exist: {log_dir}")
        return

    lines = _read_recent_jsonl_lines(
        log_dir,
        cfg.streamlit_log_glob,
        chunk_bytes=cfg.streamlit_log_chunk_bytes,
        max_files=2,
    )

    if not lines:
        st.write("No JSONL files yet.")
        return

    for ln in lines[-cfg.streamlit_log_tail_max_lines :]:
        _render_log(
            ln,
            render_mode=cfg.streamlit_log_renderer,
            default_expanded=cfg.streamlit_log_expanded,
            tz_mode=cfg.streamlit_log_tz,
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


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Bootstrap diagnostics section                                              │
# ╰────────────────────────────────────────────────────────────────────────────╯
def render_bootstrap_diagnostics() -> None:
    """
    Display initialization latencies and failure counters recorded
    by quantum.infrastructure.observability.bootstrap.diagnostics.
    """
    st.subheader("🧩 Bootstrap Diagnostics")

    try:
        # Retrieve latency histogram quantiles
        _ = _histogram_quantiles(
            "quantum_observability_init_duration_seconds", quantiles=(0.5, 0.95, 0.99)
        )

        # Group histogram samples by subsystem label
        subsystems: dict[str, dict[str, float | None]] = {}
        for metric in _iter_metrics():
            if (
                getattr(metric, "name", None)
                != "quantum_observability_init_duration_seconds"
            ):
                continue
            for s in getattr(metric, "samples", ()):
                if not s.name.endswith("_bucket"):
                    continue
                subsystem = s.labels.get("subsystem") if s.labels else None  # type: ignore[attr-defined]
                if subsystem is None:
                    continue
                subsystems.setdefault(subsystem, {})

        # Compute failure counts per subsystem
        failures: dict[str, int] = {}
        for metric in _iter_metrics():
            if (
                getattr(metric, "name", None)
                != "quantum_observability_init_failures_total"
            ):
                continue
            for s in getattr(metric, "samples", ()):
                if not s.name.endswith("_total"):
                    continue
                subsystem = s.labels.get("subsystem") if s.labels else None  # type: ignore[attr-defined]
                if subsystem is None:
                    continue
                try:
                    failures[subsystem] = int(float(s.value))
                except (TypeError, ValueError):
                    failures[subsystem] = 0

        if not subsystems and not failures:
            st.info("No bootstrap diagnostics metrics collected yet.")
            st.divider()
            return

        # Render per-subsystem diagnostics table
        cols = st.columns(3)
        subs = sorted(set(subsystems.keys()) | set(failures.keys()))
        for i, subsystem in enumerate(subs):
            with cols[i % len(cols)]:
                fail_count = failures.get(subsystem, 0)
                quantiles = _histogram_quantiles(
                    "quantum_observability_init_duration_seconds",
                    quantiles=(0.5, 0.95, 0.99),
                )
                st.metric(
                    f"{subsystem.title()} Init Failures",
                    f"{fail_count}",
                    help="Number of failed initializations",
                )
                st.write(
                    {
                        k: (round(v, 3) if v is not None else None)
                        for k, v in quantiles.items()
                    }
                )

        st.divider()

    except Exception as exc:
        logging.getLogger(__name__).warning(f"Diagnostics render failed: {exc}")
        st.info("Diagnostics unavailable at this time.")
        st.divider()


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Page layout                                                                │
# ╰────────────────────────────────────────────────────────────────────────────╯
def main() -> None:
    """Main entry point for the Observability dashboard."""
    render_kpis()
    render_logging_counters()
    render_ui_latency_histograms()
    render_mt5_section()
    render_log_tail(LOG_CFG)
    render_actions()


if __name__ == "__main__":
    main()
