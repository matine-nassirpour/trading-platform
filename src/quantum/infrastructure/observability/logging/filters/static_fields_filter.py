import logging


class StaticFieldsFilter(logging.Filter):
    """
    Injects stable fields (service_name / namespace / version) into each LogRecord,
    so that the formatter doesn't have to read environment variables.
    """

    def __init__(
        self, *, service_name: str, service_namespace: str, service_version: str
    ) -> None:
        super().__init__()
        self._service_name = service_name
        self._service_namespace = service_namespace
        self._service_version = service_version

    def filter(self, record: logging.LogRecord) -> bool:
        # Do not overwrite if already explicitly provided in the record
        if not hasattr(record, "service_name"):
            record.service_name = self._service_name
        if not hasattr(record, "service_namespace"):
            record.service_namespace = self._service_namespace
        if not hasattr(record, "service_version"):
            record.service_version = self._service_version
        return True
