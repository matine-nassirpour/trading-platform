from prometheus_client import Counter, Gauge

pipeline_up = Gauge("quantum_pipeline_up", "0/1 end-to-end health")
otel_tracing_up = Gauge("quantum_tracing_up", "0/1 tracer init & export ok")
logging_sink_up = Gauge("quantum_logging_sink_up", "0/1 partitioned/audit writable")
logging_disk_errors_total = Counter(
    "quantum_logging_disk_errors_total", "Disk write errors"
)
logging_file_rotations_total = Counter(
    "quantum_logging_file_rotations_total", "Partitioned JSONL handler rollovers"
)

# Granularity by pillar
pipeline_logging_ok = Gauge(
    "quantum_pipeline_logging_ok", "0/1 logging initialized & writable"
)
pipeline_tracing_ok = Gauge(
    "quantum_pipeline_tracing_ok", "0/1 tracing initialized & exporter ready"
)
pipeline_metrics_http_ok = Gauge(
    "quantum_pipeline_metrics_http_ok", "0/1 metrics HTTP server running"
)

# Log schema validation errors
logging_schema_validation_errors_total = Counter(
    "quantum_logging_schema_validation_errors_total",
    "Total log schema validation errors",
)
