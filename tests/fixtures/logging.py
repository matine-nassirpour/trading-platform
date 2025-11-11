import json
import logging
import os
import time

from collections.abc import Callable
from contextlib import suppress
from pathlib import Path

import pytest

from tests.support.logging_utils import close_all_handlers, read_tail_complete_lines


@pytest.fixture
def cap_config_logs(caplog):
    """
    Capture all logs emitted by the Quantum configuration subsystem.
    """
    caplog.set_level(logging.DEBUG, logger="quantum.config")
    yield caplog


@pytest.fixture(scope="function")
def no_rate_limit_no_sampling():
    """
    Disable INFO sampling and rate limiting for tests that assert presence of logs.

    This reduces flakiness for tests that need to observe records deterministically.
    """
    prev = {
        "QUANTUM_LOG_RATELIMIT": os.environ.get("QUANTUM_LOG_RATELIMIT"),
        "QUANTUM_LOG_RPS": os.environ.get("QUANTUM_LOG_RPS"),
        "QUANTUM_LOG_SAMPLE_INFO": os.environ.get("QUANTUM_LOG_SAMPLE_INFO"),
    }
    os.environ["QUANTUM_LOG_RATELIMIT"] = "0"
    os.environ["QUANTUM_LOG_RPS"] = "1000000"
    os.environ["QUANTUM_LOG_SAMPLE_INFO"] = ""
    try:
        yield
    finally:
        for k, v in prev.items():
            if v is None:
                with suppress(KeyError):
                    del os.environ[k]
            else:
                os.environ[k] = v


@pytest.fixture(autouse=True)
def _auto_cleanup_handlers():
    """
    Auto-use fixture: if a test forgets to close the pipeline,
    we clean up the handlers after each test to avoid FD leaks.

    Cost note: this scans the logger registry per test; keep it lightweight in your
    code under test to avoid registering an excessive number of loggers.
    """
    yield
    close_all_handlers()


@pytest.fixture(scope="function")
def read_jsonl():
    """
    Return a function: (base_dir, pattern, chunk_bytes=...) -> list[dict]
    Reads the latest JSON objects from JSONL files (tail), skipping invalid lines.
    """

    def _reader(
        base_dir: Path, pattern: str = "events-*.jsonl", *, chunk_bytes: int = 256_000
    ) -> list[dict]:
        files = sorted(
            Path(base_dir).rglob(pattern),
            key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
            reverse=False,  # oldest → newest
        )
        out: list[dict] = []
        for fp in files:
            for line in read_tail_complete_lines(fp, chunk_bytes=chunk_bytes):
                with suppress(json.JSONDecodeError, TypeError):
                    out.append(json.loads(line))
        return out

    return _reader


@pytest.fixture(scope="function")
def assert_jsonl_tail(read_jsonl):
    """
    Return a convenient assertion function on the JSONL tail.

    Usage:
        assert_jsonl_tail(
            base_dir,
            match=lambda obj: bool,
            min_count=1,
            pattern="events-*.jsonl",
            timeout_s=1.5,
            poll_s=0.05,
        ) -> list[dict]
    """

    def _assert(
        base_dir: Path,
        *,
        match: Callable[[dict], bool],
        min_count: int = 1,
        pattern: str = "events-*.jsonl",
        timeout_s: float = 1.5,
        poll_s: float = 0.05,
    ) -> list[dict]:
        deadline = time.time() + timeout_s
        last: list[dict] = []
        while time.time() < deadline:
            objs = read_jsonl(base_dir, pattern=pattern)
            last = objs
            hits = [o for o in objs if _safe_bool(match, o)]
            if len(hits) >= min_count:
                return hits
            time.sleep(poll_s)
        # Failure → explicit raise with hint
        raise AssertionError(
            f"Expected at least {min_count} matching JSON logs in tail, "
            f"got {len([o for o in last if _safe_bool(match, o)])}.\n"
            f"Scanned files under: {base_dir} (pattern={pattern})"
        )

    return _assert


def _safe_bool(fn: Callable[[dict], bool], obj: dict) -> bool:
    with suppress(Exception):
        return bool(fn(obj))
    return False
