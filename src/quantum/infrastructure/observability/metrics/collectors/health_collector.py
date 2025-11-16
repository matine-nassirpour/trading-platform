from prometheus_client import Counter, Gauge, Info

from quantum.infrastructure.config.runtime.manager import ConfigManager

# ╭───────────────────────────────────────────────────────────────────────────╮
# │ Service / Build metadata                                                  │
# ╰───────────────────────────────────────────────────────────────────────────╯
build_info = Info("quantum_build", "Build/Service info")


def refresh_build_info_from_env() -> None:
    """Refresh build and environment info (static Prometheus labels)."""
    core_settings = ConfigManager.load()
    build_info.info(
        {
            "service_name": core_settings.quantum_app_name,
            "service_version": core_settings.quantum_app_version,
            "service_namespace": core_settings.quantum_ns,
            "env": core_settings.quantum_env,
        }
    )


refresh_build_info_from_env()


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
