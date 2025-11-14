import logging


class StaticFieldsFilter(logging.Filter):
    """
    Enriches log records with static service metadata.
    """

    def __init__(
        self, *, env: str, namespace: str, app_name: str, version: str
    ) -> None:
        super().__init__()
        self.env = env
        self.namespace = namespace
        self.app_name = app_name
        self.version = version

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Ensures service metadata fields are present on each record.
        Does not overwrite fields already explicitly defined.
        """
        record.env = getattr(record, "env", self.env)
        record.service_namespace = getattr(record, "service_namespace", self.namespace)
        record.service_name = getattr(record, "service_name", self.app_name)
        record.service_version = getattr(record, "service_version", self.version)
        return True
