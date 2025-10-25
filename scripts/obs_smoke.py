"""
Observability smoke test (E2E runtime)

- Starts the base (init_observability)
- Produces spans/logs/events
- Checks in-memory metrics
- Checks files (partition + rollover)
- Checks redaction and presence of key fields
- Checks for a valid audit file
- (Optional) Checks the /metrics endpoint
- Verifies severity mapping (WARNING→WARN, CRITICAL→FATAL) and severity_number bounds
"""

import argparse
import json
import logging
import os
import socket
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, SupportsFloat, SupportsIndex, cast

from opentelemetry import trace

from quantum.infrastructure.observability.bootstrap.health_registry import (
    get_health_registry,
)
from quantum.infrastructure.observability.bootstrap.init_manager import (
    init_observability,
    shutdown_observability,
)
from quantum.infrastructure.observability.logging.event_emitter import emit_event
from quantum.infrastructure.observability.metrics.collectors import (
    health_collector as m,
)
from quantum.infrastructure.observability.tracing.correlation.correlation_id import (
    correlation_context,
    new_correlation_id,
)
from quantum.infrastructure.observability.tracing.propagation import (
    baggage_context_from_ids,
)

# ╭───────────────────────────────────────────────────────────────────────────╮
# │ Internal utilities                                                        │
# ╰───────────────────────────────────────────────────────────────────────────╯
NumberLike = float | int | str | bytes
Floatable = SupportsFloat | SupportsIndex | str | bytes | bytearray | memoryview


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _latest_matching(root: Path, pattern: str) -> Path | None:
    """
    Returns the most recent file (mtime) matching `pattern` under `root`.
    """
    candidates = list(root.rglob(pattern))
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def _all_matching(root: Path, pattern: str) -> list[Path]:
    """Returns all files matching pattern under root, sorted by mtime ascending."""
    files = list(root.rglob(pattern))
    files.sort(key=lambda p: p.stat().st_mtime)
    return files


def _any_matching(root: Path, pattern: str) -> Path | None:
    for p in root.rglob(pattern):
        return p
    return None


def _gauge_value(g: Any) -> float:
    """
    Returns the value of a prometheus_client Gauge.
    """
    maybe_get = getattr(getattr(g, "_value", None), "get", None)
    if not callable(maybe_get):
        return -1.0

    get_value = cast(Callable[[], NumberLike], maybe_get)
    try:
        return float(get_value())
    except (TypeError, ValueError, OverflowError, RuntimeError):
        return -1.0


def _counter_value(c: Any) -> float:
    """Returns the value of a prometheus_client Counter."""
    maybe_get = getattr(getattr(c, "_value", None), "get", None)
    if not callable(maybe_get):
        return -1.0

    get_value = cast(Callable[[], Floatable], maybe_get)
    try:
        return float(get_value())
    except (
        AttributeError,
        TypeError,
        ValueError,
        RuntimeError,
        KeyError,
        OverflowError,
    ):
        return -1.0


def _label_from_filename() -> str:
    stem = Path(__file__).stem.lower()
    return "SMOKE" if "smoke" in stem else "SELFTEST"


# ╭───────────────────────────────────────────────────────────────────────────╮
# │ Main E2E pipeline test                                                    │
# ╰───────────────────────────────────────────────────────────────────────────╯
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

    label = _label_from_filename()

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

        # Disable sampling and rate limiting to ensure all test logs pass
        os.environ["QUANTUM_LOG_SAMPLE_INFO"] = ""  # disable INFO sampling
        os.environ["QUANTUM_LOG_RATELIMIT"] = "0"  # disable rate limiting

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
            os.environ["QUANTUM_LOG_DEEP_PROBE"] = "1"
        else:
            port = None
            os.environ["QUANTUM_METRICS_PORT"] = "0"

        # Pipeline launch
        init_observability(force=True)
        registry = get_health_registry()
        log = logging.getLogger("selftest")
        tracer = trace.get_tracer("quantum.selftest")

        errs: list[str] = []

        try:
            with correlation_context(new_correlation_id()):
                with baggage_context_from_ids():
                    with tracer.start_as_current_span("selftest.span") as sp:
                        sp.set_attribute("probe", True)
                        # assert contextual enrichment (at least present on the SDK side)
                        attrs = getattr(sp, "attributes", None)
                        if isinstance(attrs, dict):
                            if "quantum.run_id" not in attrs:
                                errs.append("span missing attribute quantum.run_id")
                                if "quantum.correlation_id" not in attrs:
                                    errs.append(
                                        "span missing attribute quantum.correlation_id"
                                    )

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
                        log.info("inside span", extra={"attrs": {"in_span": True}})
                        log.warning("severity probe warning")
                        log.critical("severity probe critical")

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

            # HealthRegistry metrics validation
            def _g(gauge):
                return float(gauge._value.get())

            # Core gauges
            logging_ok = _g(registry.pipeline_logging_ok)
            tracing_ok = _g(registry.pipeline_tracing_ok)
            metrics_ok = (
                _g(registry.pipeline_metrics_http_ok) if args.with_http_metrics else 0.0
            )
            pipeline_up = _g(registry.pipeline_up)

            # pipeline_up now depends on logging_ok, tracing_ok and metrics_ok
            expected_pipeline_up = (
                1.0
                if (logging_ok == 1.0 and tracing_ok == 1.0 and metrics_ok == 1.0)
                else 0.0
            )

            if logging_ok != 1.0:
                errs.append("pipeline_logging_ok != 1")
            if tracing_ok != 1.0:
                errs.append("pipeline_tracing_ok != 1")
            if args.with_http_metrics and metrics_ok != 1.0:
                errs.append("pipeline_metrics_http_ok != 1 (HTTP)")

            if pipeline_up != expected_pipeline_up:
                errs.append(
                    f"pipeline_up = {pipeline_up}, expected {expected_pipeline_up} "
                    f"(logging_ok={logging_ok}, tracing_ok={tracing_ok}, metrics_ok={metrics_ok})"
                )

            # Asserts: log files + rollover
            latest_events = _latest_matching(log_dir, "events-*.jsonl")
            if not latest_events:
                errs.append("no events-*.jsonl file generated")
            # .part1 exists?
            if not list(log_dir.rglob("*.part1.jsonl")):
                errs.append("rollover not detected (missing .part1.jsonl)")

            # Asserts: JSON content + redaction + key fields + severity mapping
            events_files = _all_matching(log_dir, "events-*.jsonl")
            if not events_files:
                errs.append("no events-*.jsonl file generated (scan)")
            else:
                found_selftest = None
                found_warn = None
                found_crit = None

                for fp in events_files:
                    with open(fp, encoding="utf-8") as f:
                        for line in f:
                            try:
                                js = json.loads(line)
                            except json.JSONDecodeError:
                                continue  # skip invalid JSON lines
                            msg = js.get("message")
                            if msg == "selftest start" and not found_selftest:
                                found_selftest = js
                            elif msg == "severity probe warning" and not found_warn:
                                found_warn = js
                            elif msg == "severity probe critical" and not found_crit:
                                found_crit = js
                            # optimisation: stop early si on a tout
                            if found_selftest and found_warn and found_crit:
                                break
                    if found_selftest and found_warn and found_crit:
                        break

                # selftest start basic checks (schema, redaction, fields)
                if not found_selftest:
                    errs.append("could not find 'selftest start' log entry")
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
                        if k not in found_selftest:
                            errs.append(f"missing field '{k}' in JSON log")
                    if "correlation_id" not in found_selftest:
                        errs.append("correlation_id missing in JSON log")
                    attrs = found_selftest.get("attrs", {})
                    if attrs.get("secret") != "[REDACTED]":
                        errs.append(
                            "redaction not applied (attrs.secret != [REDACTED])"
                        )

                def _check_severity(obj: dict, expected_level: str, expected_num: int):
                    if not obj:
                        errs.append(
                            f"missing log for severity probe ({expected_level})"
                        )
                        return
                    lvl = obj.get("level")
                    if lvl != expected_level:
                        errs.append(
                            f"level mapping failed: expected {expected_level}, got {lvl!r}"
                        )
                    num = obj.get("severity_number")
                    if not isinstance(num, int):
                        errs.append("severity_number missing or not an int")
                    else:
                        if not (1 <= num <= 24):
                            errs.append(
                                f"severity_number out of range [1..24]: got {num}"
                            )
                        # stricter check (expected OTel mapping used in code)
                        if num != expected_num:
                            errs.append(
                                f"unexpected severity_number for {expected_level}: got {num}, expected {expected_num}"
                            )

                _check_severity(found_warn, "WARN", 13)
                _check_severity(found_crit, "FATAL", 21)

            # Check that at least one log UNDER SPAN contains trace_id/span_id
            has_trace = False
            for fp in _all_matching(log_dir, "events-*.jsonl"):
                with open(fp, encoding="utf-8") as f:
                    for line in f:
                        try:
                            js = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if (
                            js.get("message") == "inside span"
                            and js.get("trace_id")
                            and js.get("span_id")
                        ):
                            has_trace = True
                            break
                if has_trace:
                    break
            if not has_trace:
                errs.append("missing trace_id/span_id on 'inside span' log")

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
                except json.JSONDecodeError:
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

            # Trace exporter active (console->0, none->0, otlp->1 if built)
            exp = os.environ.get("QUANTUM_TRACE_EXPORTER", "console")
            exp_active = _gauge_value(m.tracing_exporter_status)
            if exp == "otlp":
                if not exp_active == 1.0:
                    errs.append("tracing_exporter_status != 1 with exporter=otlp")
            else:
                if not exp_active == 0.0:
                    errs.append(
                        "tracing_exporter_status should be 0 with exporter!=otlp"
                    )

            # Compteur de redaction > 0
            if _counter_value(m.logging_redactions_total) <= 0.0:
                errs.append("logging_redactions_total did not increase")

        finally:
            # Always shut down cleanly to free handles (Windows!)
            shutdown_observability()

        # Result
        if errs:
            print(f"{label}: FAIL")
            for e in errs:
                print(" -", e)
            # show locations for manual inspection
            print(f"logs:   {log_dir}")
            print(f"audit:  {audit_dir}")
            sys.exit(1)

        print(f"{label}: OK")
        print(f"logs:   {log_dir}")
        print(f"audit:  {audit_dir}")


if __name__ == "__main__":
    main()
