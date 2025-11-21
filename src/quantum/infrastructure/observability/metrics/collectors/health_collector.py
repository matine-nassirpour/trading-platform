from prometheus_client import Counter, Gauge

# ╭───────────────────────────────────────────────────────────────────────────╮
# │ Tracing subsystem metrics                                                 │
# ╰───────────────────────────────────────────────────────────────────────────╯
tracing_exporter_status = Gauge(
    "quantum_tracing_exporter_status",
    "Indicates whether the active exporter is operational (1=ok, 0=inactive).",
)

# ╭───────────────────────────────────────────────────────────────────────────╮
# │ Logging subsystem metrics                                                 │
# ╰───────────────────────────────────────────────────────────────────────────╯
logging_file_rotations = Counter(
    "quantum_logging_file_rotations",
    "Total number of JSONL handler rollovers performed.",
)
logging_redactions_total = Counter(
    "quantum_logging_redactions_total",
    "Total number of log redactions performed for sensitive data.",
)
logging_schema_validation_errors_total = Counter(
    "quantum_logging_schema_validation_errors_total",
    "Total number of log schema validation errors encountered.",
)
logging_disk_errors = Counter(
    "quantum_logging_disk_errors",
    "Total number of disk write or I/O errors in logging subsystem.",
)
