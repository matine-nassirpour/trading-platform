import pytest


@pytest.fixture(autouse=True)
def _reset_config_state():
    """
    Automatically reset ConfigManager caches and ConfigState between tests.

    Ensures no residual environment or LRU cache contamination between tests,
    preserving hermeticity for configuration-dependent modules.
    """
    from quantum.infrastructure.config.runtime.manager import ConfigManager
    from quantum.infrastructure.config.runtime.state import ConfigState

    ConfigManager.clear_caches()
    ConfigState.instance().reset()
    yield
    ConfigManager.clear_caches()
    ConfigState.instance().reset()
