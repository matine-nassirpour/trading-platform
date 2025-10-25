import logging


class StaticFieldsFilter(logging.Filter):
    """
    Enriches log records with static service metadata.
    """

    def __init__(
        self, *, service_name: str, service_namespace: str, service_version: str
    ) -> None:
        super().__init__()
        self.service_name = service_name
        self.service_namespace = service_namespace
        self.service_version = service_version

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Ensures service metadata fields are present on each record.
        Does not overwrite fields already explicitly defined.
        """
        if not hasattr(record, "service_name"):
            record.service_name = self.service_name
        if not hasattr(record, "service_namespace"):
            record.service_namespace = self.service_namespace
        if not hasattr(record, "service_version"):
            record.service_version = self.service_version
        return True
