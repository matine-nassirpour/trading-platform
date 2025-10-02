import logging

from apps.cli.bootstrap import init_cli
from quantum.interface.cli.entrypoints import reconcile, refresh_market

logger = logging.getLogger(__name__)


# Small temporary stubs (while waiting for the real use cases Application)
class _RefreshMarketStub:
    def execute(self, *, symbol: str | None = None) -> None:
        logger.info("Refreshing market%s...", f" for {symbol}" if symbol else "")


class _ReconcileStub:
    def execute(self) -> None:
        logger.info("Reconciling positions/orders/deals...")


def main() -> None:
    init_cli()
    logger.info("Quantum trading core started.")

    refresh_market(_RefreshMarketStub(), symbol=None)
    reconcile(_ReconcileStub())


if __name__ == "__main__":
    main()
