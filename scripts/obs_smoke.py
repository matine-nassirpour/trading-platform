"""
Observability smoke test (E2E runtime)

- Starts the base (init_observability)
- Produces spans/logs/events
- Checks in-memory metrics
- Checks files (partition + rollover)
- Checks redaction and presence of key fields
- Checks for a valid audit file
- (Optional) Checks the /metrics endpoint

Usage:
python scripts/obs_smoke.py
python scripts/obs_smoke.py --with-http-metrics
python scripts/obs_smoke.py --exporter otlp --protocol http --endpoint http://127.0.0.1:4318
"""

import argparse
import json
import logging
import os
import socket
import sys
import tempfile
import time
from pathlib import Path

from opentelemetry import trace

from quantum.infrastructure.observability.init_observability import (
    init_observability,
    shutdown_observability,
)
from quantum.infrastructure.observability.logging.event_emitter import emit_event
from quantum.infrastructure.observability.metrics import health as m
from quantum.infrastructure.observability.tracing.propagation import (
    refresh_baggage_from_context,
)
from quantum.shared.correlation.correlation_id import (
    correlation_context,
    new_correlation_id,
)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _read_last_jsonl_line(p: Path) -> dict | None:
    """
    Reads the LAST JSON line of a .jsonl (tail), robust even for large files.
    """
    try:
        with open(p, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            if size == 0:
                return None
            f.seek(max(0, size - 65536), os.SEEK_SET)
            data = f.read().decode("utf-8", "replace").splitlines()
            for line in reversed(data):
                line = line.strip()
                if line:
                    try:
                        return json.loads(line)
                    except Exception:
                        continue
    except Exception:
        return None
    return None


def _latest_matching(root: Path, pattern: str) -> Path | None:
    """
    Returns the most recent file (mtime) matching `pattern` under `root`.
    """
    candidates = list(root.rglob(pattern))
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def _any_matching(root: Path, pattern: str) -> Path | None:
    for p in root.rglob(pattern):
        return p
    return None


def _gauge_value(g) -> float:
    """
    Returns the value of a prometheus_client (best-effort) Gauge.
    """
    try:
        return float(g._value.get())  # type: ignore[attr-defined]
    except Exception:
        return -1.0


def _label_from_filename() -> str:
    stem = Path(__file__).stem.lower()
    return "SMOKE" if "smoke" in stem else "SELFTEST"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--with-http-metrics",
        action="store_true",
        help="Start the /metrics endpoint and check the probe.",
    )
    ap.add_argument(
        "--exporter",
        choices=["console", "otlp", "none"],
        default="console",
        help="Export tracing to test (default: console).",
    )
    ap.add_argument(
        "--protocol",
        choices=["http", "grpc"],
        default="http",
        help="OTLP protocol if exporter=otlp.",
    )
    ap.add_argument(
        "--endpoint",
        default="http://127.0.0.1:4318",
        help="OTLP endpoint (http) or host:port (grpc).",
    )
    ap.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="Fails if there are 'nearing size threshold' warnings (not implemented here).",
    )
    args = ap.parse_args()

    LABEL = _label_from_filename()

    # Isolated space for this test
    with tempfile.TemporaryDirectory(prefix="quantum_obs_") as tmpd:
        tmp = Path(tmpd)
        log_dir = tmp / "_logs"
        audit_dir = tmp / "_audit"
        log_dir.mkdir(parents=True, exist_ok=True)
        audit_dir.mkdir(parents=True, exist_ok=True)

        # Clean ENVs (& aggressive to force a rollover)
        os.environ["QUANTUM_APP_NAME"] = "obs_selftest"
        os.environ["QUANTUM_APP_VERSION"] = "0.1.0+selftest"
        os.environ["QUANTUM_ENV"] = "dev"
        os.environ["QUANTUM_NS"] = "quantum"

        os.environ["QUANTUM_LOG_LEVEL"] = "INFO"
        os.environ["QUANTUM_LOG_DIR"] = str(log_dir)
        os.environ["QUANTUM_AUDIT_DIR"] = str(audit_dir)

        os.environ["QUANTUM_LOG_FSYNC"] = "0"  # fsync disabled (faster)
        os.environ["QUANTUM_LOG_MAX_BYTES"] = "2048"  # rollover ~2KB
        os.environ["QUANTUM_LOG_WARN_BYTES"] = "0"
        os.environ["QUANTUM_TRACE_SAMPLE"] = "1.0"
        os.environ["QUANTUM_TRACE_EXPORTER"] = args.exporter

        os.environ.setdefault("QUANTUM_AUDIT_EVENTS_VERSION", "v1")
        os.environ.setdefault("QUANTUM_AUDIT_EVENTS", "order_submit_v1")

        if args.exporter == "otlp":
            os.environ["QUANTUM_TRACE_OTLP_PROTOCOL"] = args.protocol
            os.environ["QUANTUM_TRACE_OTLP_ENDPOINT"] = args.endpoint
            if args.protocol == "grpc":
                # local default: insecure
                os.environ["QUANTUM_TRACE_OTLP_INSECURE"] = "1"

        if args.with_http_metrics:
            port = _free_port()
            os.environ["QUANTUM_METRICS_PORT"] = str(port)
            os.environ["QUANTUM_METRICS_ADDR"] = "127.0.0.1"
        else:
            port = None
            os.environ["QUANTUM_METRICS_PORT"] = "0"

        # Pipeline launch
        init_observability(force=True)
        log = logging.getLogger("selftest")
        tracer = trace.get_tracer("quantum.selftest")

        errs: list[str] = []

        try:
            with correlation_context(new_correlation_id()):
                refresh_baggage_from_context()
                with tracer.start_as_current_span("selftest.span") as sp:
                    sp.set_attribute("probe", True)

                    # departure log with secret to write
                    log.info(
                        "selftest start",
                        extra={
                            "attrs": {
                                "probe": "ok",
                                "secret": "thisisafakesecret",  # pragma: allowlist secret
                            }
                        },
                    )

                    # audit event (whitelisted)
                    emit_event(
                        {
                            "event_name": "order_submit_v1",
                            "event_version": "v1",
                            "order_id": "st-1",
                            "symbol": "EURUSD",
                            "side": "buy",
                            "qty": 1.0,
                            "price": 1.23456,
                            "ts": int(time.time() * 1000),
                        }
                    )

                    # flood ~3KB to trigger rollover .part1
                    payload = "X" * 256
                    for i in range(40):
                        log.info(f"fill {i} {payload}")

            # Asserts: in-memory metrics
            if _gauge_value(m.pipeline_up) != 1.0:
                errs.append("pipeline_up != 1")
            if _gauge_value(m.pipeline_logging_ok) != 1.0:
                errs.append("pipeline_logging_ok != 1")
            if _gauge_value(m.pipeline_tracing_ok) != 1.0:
                errs.append("pipeline_tracing_ok != 1")
            if (
                args.with_http_metrics
                and _gauge_value(m.pipeline_metrics_http_ok) != 1.0
            ):
                errs.append("pipeline_metrics_http_ok != 1 (HTTP)")

            # Asserts: log files + rollover
            latest_events = _latest_matching(log_dir, "events-*.jsonl")
            if not latest_events:
                errs.append("no events-*.jsonl file generated")
            # .part1 exists?
            if not list(log_dir.rglob("*.part1.jsonl")):
                errs.append("rollover not detected (missing .part1.jsonl)")

            # Asserts: JSON content (last line) + redaction + key fields
            if latest_events:
                last = _read_last_jsonl_line(latest_events)
                if not last:
                    errs.append("Unable to read last JSONL line")
                else:
                    must_fields = [
                        "service_name",
                        "service_namespace",
                        "service_version",
                        "timestamp",
                        "level",
                        "logger",
                        "message",
                        "attrs",
                    ]
                    for k in must_fields:
                        if k not in last:
                            errs.append(f"missing field '{k}' in JSON log")
                    if "correlation_id" not in last:
                        errs.append("correlation_id missing in JSON log")

                    attrs = last.get("attrs", {})
                    # the writing must have replaced the value
                    if attrs.get("secret") == "s3cr3t":
                        errs.append("redaction not applied (attrs.secret)")

            # Asserts: Valid JSON audit file
            audit_any = _any_matching(audit_dir, "*.json")
            deadline = time.time() + 2.0
            while audit_any is None and time.time() < deadline:
                time.sleep(0.05)
                audit_any = _any_matching(audit_dir, "*.json")

            if not audit_any:
                errs.append("no audit file generated")
            else:
                try:
                    js = json.loads(audit_any.read_text(encoding="utf-8"))
                    if js.get("event_name") != "order_submit_v1":
                        errs.append("invalid audit file (event_name)")
                except Exception:
                    errs.append("unreadable/invalid audit file")

            # (Option) ping /metrics
            if args.with_http_metrics and port is not None:
                try:
                    import urllib.request

                    url = f"http://127.0.0.1:{port}/metrics"
                    with urllib.request.urlopen(url, timeout=2.0) as resp:
                        body = resp.read().decode("utf-8", "replace")
                    if "quantum_pipeline_up 1" not in body:
                        errs.append("/metrics does not contain 'quantum_pipeline_up 1'")
                except Exception as e:
                    errs.append(f"/metrics unavailable: {e}")

        finally:
            # Always shut down cleanly to free handles (Windows!)
            shutdown_observability()

        # Result
        if errs:
            print(f"{LABEL}: FAIL")
            for e in errs:
                print(" -", e)
            # show locations for manual inspection
            print(f"logs:   {log_dir}")
            print(f"audit:  {audit_dir}")
            sys.exit(1)

        print(f"{LABEL}: OK")
        print(f"logs:   {log_dir}")
        print(f"audit:  {audit_dir}")


if __name__ == "__main__":
    main()
