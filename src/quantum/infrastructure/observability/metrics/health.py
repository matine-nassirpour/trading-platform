import os

from prometheus_client import Counter, Gauge, Info

# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Service / Build metadata (static, exported once)                            │
# ╰─────────────────────────────────────────────────────────────────────────────╯
build_info = Info("quantum_build", "Build/Service info")


def refresh_build_info_from_env() -> None:
    build_info.info(
        {
            "service_name": os.getenv("QUANTUM_APP_NAME", "unknown"),
            "service_version": os.getenv("QUANTUM_APP_VERSION", "0.0.0"),
            "service_namespace": os.getenv("QUANTUM_NS", "quantum"),
            "env": os.getenv("QUANTUM_ENV", "dev"),
        }
    )


refresh_build_info_from_env()

# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Pipeline health (overall & per pillar)                                      │
# ╰─────────────────────────────────────────────────────────────────────────────╯
pipeline_up = Gauge("quantum_pipeline_up", "0/1 end-to-end health")
pipeline_logging_ok = Gauge(
    "quantum_pipeline_logging_ok", "0/1 logging initialized & writable"
)
pipeline_tracing_ok = Gauge(
    "quantum_pipeline_tracing_ok", "0/1 tracing initialized & exporter ready"
)
pipeline_metrics_http_ok = Gauge(
    "quantum_pipeline_metrics_http_ok", "0/1 metrics HTTP server running"
)

# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Tracing subsystem                                                           │
# ╰─────────────────────────────────────────────────────────────────────────────╯
otel_tracing_up = Gauge("quantum_tracing_up", "0/1 tracer init & export ok")
tracer_exporter_active = Gauge(
    "quantum_tracer_exporter_active", "0/1 exporter configured & active"
)

# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Logging subsystem                                                           │
# ╰─────────────────────────────────────────────────────────────────────────────╯
logging_sink_up = Gauge("quantum_logging_sink_up", "0/1 partitioned/audit writable")
logging_file_rotations_total = Counter(
    "quantum_logging_file_rotations_total", "Partitioned JSONL handler rollovers"
)
logging_redactions_total = Counter(
    "quantum_logging_redactions_total", "Total log redactions performed"
)
logging_schema_validation_errors_total = Counter(
    "quantum_logging_schema_validation_errors_total",
    "Total log schema validation errors",
)
logging_disk_errors_total = Counter(
    "quantum_logging_disk_errors_total", "Disk write errors"
)
