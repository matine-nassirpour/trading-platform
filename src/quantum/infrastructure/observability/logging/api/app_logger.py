import logging

APPLICATION_LOGGER_NAME = "quantum.app"


def get_app_logger() -> logging.Logger:
    return logging.getLogger(APPLICATION_LOGGER_NAME)
