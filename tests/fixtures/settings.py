from pathlib import Path

import pytest

from quantum.infrastructure.config.models.core import CoreSettings


@pytest.fixture
def valid_core_settings(tmp_workspace) -> CoreSettings:
    """Return a valid CoreSettings instance using the temporary workspace."""
    from quantum.infrastructure.config.runtime.manager import ConfigManager

    return ConfigManager.load(apply=False)


@pytest.fixture
def base_settings(tmp_path: Path) -> CoreSettings:
    """Return minimal Settings pointing logs under tmp_path."""
    return CoreSettings(
        quantum_app_name="test_app",
        quantum_app_version="0.0.0+test",
        quantum_env="test",
        quantum_ns="quantum",
        quantum_metrics_port=0,
    )
