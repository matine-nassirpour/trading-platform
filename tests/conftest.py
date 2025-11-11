from __future__ import annotations

import pytest

pytest_plugins = [
    "tests.fixtures.environment",
    "tests.fixtures.observability",
    "tests.fixtures.state",
    "tests.fixtures.logging",
    "tests.fixtures.settings",
]


def pytest_configure(config: pytest.Config) -> None:
    """
    Register commonly used custom markers to avoid warnings and improve test filtering.
    """
    for marker in ("unit", "filesystem", "prometheus", "otlp", "e2e"):
        config.addinivalue_line("markers", marker)
