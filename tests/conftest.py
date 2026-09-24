"""Pytest configuration: global test fixtures and patching."""

import os
import pytest

# Set at module load time to catch both pytest and unittest runs via pytest
os.environ["AGENT_OS_DISABLE_MODEL_REFRESH"] = "1"


@pytest.fixture(scope="session", autouse=True)
def disable_background_model_refresh():
    """Ensure background model refresh is disabled for all tests to prevent unpatched network and filesystem access."""
    # Already set at module load time, but this fixture ensures it's in place throughout the test session
    yield
