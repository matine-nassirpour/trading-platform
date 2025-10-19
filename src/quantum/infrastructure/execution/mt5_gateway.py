from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from quantum.infrastructure.execution._timeout_utils import timeout_guard
from quantum.infrastructure.execution.contracts import ExecutionFunctionProtocol
from quantum.infrastructure.execution.gateway_registry import (
    is_gateway_healthy,
    record_gateway_failure,
    record_gateway_success,
)
from quantum.infrastructure.execution.mappings.mt5_retcode_map import (
    map_mt5_res_to_exec,
)
from quantum.infrastructure.observability.metrics.mt5 import (
    exec_channel_latency_ms,
    exec_channel_total,
)
from quantum.infrastructure.observability.tracing.traces import get_tracer
from quantum.shared.config.config_manager import ConfigManager
from quantum.shared.types.channels import ExecutionChannel
from quantum.shared.types.execution import ExecutionCode
from quantum.shared.types.execution_result import ExecutionResult

logger = logging.getLogger(__name__)
tracer = get_tracer("infra.execution.mt5")


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Terminal init / shutdown                                                    │
# ╰─────────────────────────────────────────────────────────────────────────────╯
def init_mt5_terminal(channel: ExecutionChannel, path: str | None = None) -> bool:
    """
    Initializes and logs into a MetaTrader5 terminal for the given execution channel.

    Loads credentials (login, password, server) from ConfigManager
    and attempts a secure MT5 connection.
    """
    try:
        import MetaTrader5 as mt5  # lazy import

        creds = ConfigManager.get_mt5_credentials(channel.name)
        if not creds["login"] or not creds["server"] or not creds["password"]:
            logger.error(
                f"Missing MT5 credentials for channel {channel.name}",
                extra={"attrs": {"channel": channel.name}},
            )
            return False

        ok = mt5.initialize(
            path=path,
            login=int(creds["login"]),
            password=creds["password"],
            server=creds["server"],
        )

        if not ok:
            try:
                code, msg = mt5.last_error()
                logger.error(
                    f"MT5 initialize failed for {channel.name}",
                    extra={"attrs": {"error_code": code, "error_msg": msg}},
                )
            except Exception:
                logger.error(
                    f"MT5 initialize failed (no last_error) for {channel.name}",
                    extra={"attrs": {"path": path}},
                )
        else:
            logger.info(
                f"MT5 terminal initialized for {channel.name}",
                extra={"attrs": {"server": creds["server"], "login": creds["login"]}},
            )
        return bool(ok)

    except Exception as e:
        logger.exception(
            f"MT5 init error for {channel.name}: {type(e).__name__} {e}",
            extra={"attrs": {"path": path}},
        )
        return False


def shutdown_mt5_terminal() -> None:
    """Best-effort shutdown for the MetaTrader5 terminal."""
    try:
        import MetaTrader5 as mt5  # lazy import

        mt5.shutdown()
    except Exception:
        pass


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Main MT5 execution harness (Protocol implementation)                        │
# ╰─────────────────────────────────────────────────────────────────────────────╯


class Mt5ExecutionFunction(ExecutionFunctionProtocol):
    """
    Canonical implementation of the ExecutionFunctionProtocol for MetaTrader5.

    Provides
    --------
    - Safe, instrumented, and fault-tolerant API call execution
    - Prometheus latency and total metrics
    - OpenTelemetry traces with detailed attributes
    - Circuit breaker & health gate protection
    - Cross-platform timeout guard
    - Structured, contextual logging
    """

    def __call__(
        self,
        call: str,
        func: Callable[..., Any],
        *args: Any,
        channel: ExecutionChannel | None = None,
        **kwargs: Any,
    ) -> ExecutionResult:
        start_ms = time.time() * 1000.0
        timeout_s = ConfigManager.load().quantum_exec_timeout
        result: Any | None = None
        msg = ""
        code: ExecutionCode = ExecutionCode.FAIL

        with tracer.start_as_current_span(f"exec.{call}") as span:
            # ─── Health gate
            if channel and not is_gateway_healthy(channel):
                msg = f"Execution channel {channel.name} unhealthy — call aborted."
                logger.warning(msg)
                span.set_status("ERROR")
                return ExecutionResult(
                    code=ExecutionCode.INTERNAL_FAIL, message=msg, payload=None
                )

            try:
                with timeout_guard(timeout_s, call):
                    result = func(*args, **kwargs)
                    res_code = getattr(result, "retcode", None)
                    msg = getattr(result, "comment", "") or ""
                    code = map_mt5_res_to_exec(int(res_code or -1))
                    record_gateway_success(channel)

            except TimeoutError as e:
                msg = str(e)
                code = ExecutionCode.INTERNAL_FAIL_TIMEOUT
                record_gateway_failure(channel)
                logger.error(msg)

            except Exception as e:
                msg = f"{type(e).__name__}: {e}"
                code = ExecutionCode.INTERNAL_FAIL
                record_gateway_failure(channel)
                logger.exception(
                    f"MT5 call '{call}' crashed with exception", exc_info=e
                )

            # ─── Metrics & Observability
            dur_ms = int(time.time() * 1000.0 - start_ms)
            try:
                exec_channel_latency_ms.labels(call=call).observe(dur_ms)
                exec_channel_total.labels(call=call, code=str(code)).inc()
            except Exception:
                pass  # metrics should never break execution

            # ─── Tracing enrichment
            span.set_attribute("exec.channel", str(channel or "unknown"))
            span.set_attribute("exec.call", call)
            span.set_attribute("exec.code", str(code))
            span.set_attribute("exec.latency_ms", dur_ms)
            span.set_attribute("exec.timeout_s", timeout_s)

            if code != ExecutionCode.OK:
                from opentelemetry.trace import Status, StatusCode

                span.set_status(Status(StatusCode.ERROR, description=str(code)))

            # ─── Structured Log
            logger.info(
                "MT5 exec",
                extra={
                    "attrs": {
                        "call": call,
                        "channel": str(channel or "N/A"),
                        "code": str(code),
                        "latency_ms": dur_ms,
                        "msg": msg[:256] if msg else None,
                    }
                },
            )

            return ExecutionResult(code=code, message=msg, payload=result)
