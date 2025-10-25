import logging


class ContextFilter(logging.Filter):
    """
    Enriches log records with immutable context fields such as the current environment.
    """

    def __init__(self, env: str) -> None:
        super().__init__()
        self.env = env

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Injects the 'env' field into the LogRecord if not already present.
        """
        if not hasattr(record, "env"):
            record.env = self.env
        return True
