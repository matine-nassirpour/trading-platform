from __future__ import annotations

import logging

from collections.abc import Mapping
from contextlib import asynccontextmanager
from typing import Any

from opentelemetry.trace import Status, StatusCode

from quantum.application.ports.outbound.tracing_port import TraceHandle, TracingPort
from quantum.infrastructure.observability.drivers.observability_driver import (
    ObservabilityDriver,
)
from quantum.infrastructure.observability.logging.audit.emitter import emit_event
from quantum.infrastructure.observability.tracing.provider import get_tracer


class _HybridTraceHandle(TraceHandle):
    """
    Internal hybrid trace handle:
        - OTEL span (maybe None if tracing disabled)
        - Structured trace logs
    """

    def __init__(
        self,
        operation: str,
        logger: logging.Logger,
        span,
    ) -> None:
        self._op = operation
        self._logger = logger
        self._span = span

    async def set_attribute(self, key: str, value: Any) -> None:
        if self._span is not None:
            try:
                self._span.set_attribute(key, value)
            except Exception as err:
                self._logger.debug(
                    "[otel:set_attribute] ignored OTEL error",
                    extra={"attrs": {"error": str(err), "key": key}},
                )

    async def record_exception(self, exc: BaseException) -> None:
        if self._span is not None:
            try:
                self._span.record_exception(exc)
                self._span.set_status(Status(StatusCode.ERROR, str(exc)))
            except Exception as err:
                self._logger.debug(
                    "[otel:record_exception] ignored OTEL error",
                    extra={"attrs": {"error": str(err)}},
                )

        # structured log
        self._logger.error(
            f"[trace:{self._op}] exception recorded",
            extra={"attrs": {"type": type(exc).__name__, "message": str(exc)}},
        )

    async def end(self) -> None:
        if self._span is not None:
            try:
                self._span.end()
            except Exception as err:
                self._logger.debug(
                    "[otel:end] ignored OTEL error",
                    extra={"attrs": {"error": str(err)}},
                )


class TracingDriver(TracingPort):
    """
    Concrete hybrid tracing adapter.

    Features:
      - OTEL spans (if provider active)
      - Structured logs for every trace
      - Automatic correlation_id / run_id injection
      - Audit events for failures
      - Clean Architecture compliant (no infrastructure leakage)
    """

    def __init__(self, obs: ObservabilityDriver) -> None:
        self._obs = obs
        self._logger = logging.getLogger("quantum.observability.trace")

    # --------------------------------------------------------------------------
    # trace() — async context manager
    # --------------------------------------------------------------------------
    @asynccontextmanager
    async def trace(
        self,
        operation: str,
        /,
        *,
        attributes: Mapping[str, Any] | None = None,
    ):
        """
        Hybrid trace:
            - start OTEL span
            - structured log: trace-start
            - structured log: trace-end
        """

        correlation_id = self._obs.ensure_correlation_id()
        run_id = self._obs.ensure_run_id()

        # OTEL span
        tracer = get_tracer("app.tracing", version="1.0.0")
        span = tracer.start_span(operation)

        if attributes:
            for k, v in attributes.items():
                try:
                    span.set_attribute(k, v)
                except Exception as err:
                    self._logger.debug(
                        "[otel:set_attribute] ignored OTEL error",
                        extra={"attrs": {"error": str(err), "key": k}},
                    )

        # enrich with IDs
        span.set_attribute("quantum.run_id", run_id)
        span.set_attribute("quantum.correlation_id", correlation_id)

        handle = _HybridTraceHandle(operation, self._logger, span)

        # structured log: start
        self._logger.info(
            f"[trace:{operation}] started",
            extra={
                "attrs": {
                    "operation": operation,
                    "run_id": run_id,
                    "correlation_id": correlation_id,
                    "attributes": dict(attributes or {}),
                }
            },
        )

        try:
            yield handle
        except BaseException as exc:
            # auto error recording
            await handle.record_exception(exc)
            raise
        finally:
            await handle.end()

            # structured log: end
            self._logger.info(
                f"[trace:{operation}] ended",
                extra={
                    "attrs": {
                        "operation": operation,
                        "run_id": run_id,
                        "correlation_id": correlation_id,
                    }
                },
            )

    # --------------------------------------------------------------------------
    # record_failure() — hybrid error reporting
    # --------------------------------------------------------------------------
    async def record_failure(
        self,
        operation: str,
        exc: BaseException,
        /,
        *,
        attributes: Mapping[str, Any] | None = None,
    ) -> None:
        """
        Hybrid error reporting:
            - span(ERROR)
            - structured log
            - audit event
        """

        correlation_id = self._obs.ensure_correlation_id()
        run_id = self._obs.ensure_run_id()

        # OTEL span (one-shot)
        tracer = get_tracer("app.tracing", version="1.0.0")
        span = tracer.start_span(f"{operation}.failure")
        try:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            span.set_attribute("quantum.run_id", run_id)
            span.set_attribute("quantum.correlation_id", correlation_id)
            if attributes:
                for k, v in attributes.items():
                    span.set_attribute(k, v)
        finally:
            span.end()

        # structured log
        self._logger.error(
            f"[failure:{operation}] {type(exc).__name__}: {exc}",
            extra={
                "attrs": {
                    "operation": operation,
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                    "run_id": run_id,
                    "correlation_id": correlation_id,
                    **(attributes or {}),
                }
            },
        )

        # audit event (immutable)
        emit_event(
            {
                "event_name": "system_error_v1",
                "operation": operation,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "run_id": run_id,
                "correlation_id": correlation_id,
                "attrs": dict(attributes or {}),
            },
            level=logging.ERROR,
        )
