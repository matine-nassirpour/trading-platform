import logging

from apps.cli.bootstrap import init_cli
from quantum.interfaces.cli.entrypoints import reconcile, refresh_market

logger = logging.getLogger(__name__)


# Small temporary stubs (while waiting for the real use cases Application)
class _RefreshMarketStub:
    def execute(self, *, symbol: str | None = None) -> None:
        logger.info("Refreshing markets...", f" for {symbol}" if symbol else "")


class _ReconcileStub:
    def execute(self) -> None:
        logger.info("Reconciling positions/orders/deals...")


def main() -> None:
    init_cli()
    try:
        logger.info("Quantum trading platform started.")
        refresh_market(_RefreshMarketStub(), symbol=None)
        reconcile(_ReconcileStub())
    finally:
        # clean shutdown to avoid orphaned handlers in tests/e2e
        from quantum.infrastructure.observability.bootstrap.init_manager import (
            shutdown_observability,
        )

        shutdown_observability()


if __name__ == "__main__":
    main()
