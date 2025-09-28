import logging

NOISY_LOGGERS = {
    "urllib3.connectionpool",
    "requests.packages.urllib3.connectionpool",
    "opentelemetry.sdk._logs",
    "opentelemetry.sdk.trace",
    "opentelemetry.sdk.trace.export",
}


class IgnoreLibrariesFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return all(not record.name.startswith(n) for n in NOISY_LOGGERS)


class SchemaVersionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.log_schema_version = "v1"
        return True


class LoggingContextFilter(logging.Filter):
    def __init__(self, env: str) -> None:
        super().__init__()
        self.env = env

    def filter(self, record: logging.LogRecord) -> bool:
        record.env = self.env
        return True
