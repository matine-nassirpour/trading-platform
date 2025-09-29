import io
import logging
from datetime import datetime, timezone
from pathlib import Path

from quantum.fundation.time.naming import partition_path_components


class PartitionedJSONLFileHandler(logging.Handler):
    """
    Writes JSON logs to partitioned JSONL files:
    <base>/<env>/<namespace>/<app>/<YYYY>/<MM>/<DD>/<HH>/events-YYYYMMDD-HH.jsonl
    """

    def __init__(
        self,
        base_dir: str,
        app: str,
        environment: str,
        namespace: str,
        encoding: str = "utf-8",
    ) -> None:
        super().__init__()
        self.base_dir = Path(base_dir)
        self.app = app
        self.environment = environment
        self.namespace = namespace
        self.encoding = encoding

        self._current_path: Path | None = None
        self._fh: io.TextIOWrapper | None = None

    def emit(self, record: logging.LogRecord) -> None:
        try:
            # 1) format record via attached formatter (JsonFormatter) -> string
            msg = self.format(record)
        except (ValueError, TypeError):
            self.handleError(record)
            return

        try:
            # 2) compute partition path from record.created
            dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
            yyyy, mm, dd, hh = partition_path_components(dt)
            dir_path = (
                self.base_dir
                / self.environment
                / self.namespace
                / self.app
                / yyyy
                / mm
                / dd
                / hh
            )
            filename = f"events-{yyyy}{mm}{dd}-{hh}.jsonl"
            file_path = dir_path / filename

            # 3) reopen file on hour change
            if file_path != self._current_path:
                self._reopen(file_path)

            # 4) write a single JSON line
            assert self._fh is not None
            self._fh.write(msg + "\n")
            self._fh.flush()
        except (OSError, ValueError):
            self.handleError(record)

    def _reopen(self, path: Path) -> None:
        if self._fh:
            try:
                self._fh.flush()
                self._fh.close()
            except (OSError, ValueError):
                pass
        path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(path, "a", encoding=self.encoding)
        self._current_path = path

    def close(self) -> None:
        try:
            if self._fh:
                self._fh.flush()
                self._fh.close()
        except (OSError, ValueError):
            pass
        finally:
            self._fh = None
            super().close()
