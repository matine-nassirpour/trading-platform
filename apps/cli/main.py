import logging

from quantum.bootstrap import init_observability

logger = logging.getLogger(__name__)


def main() -> None:
    init_observability(app_name="python_core", environment="dev", namespace="quantum")
    logger.info("Quantum trading core started.")
    # TODO: main logic


if __name__ == "__main__":
    main()
