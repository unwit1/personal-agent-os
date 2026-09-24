"""Test suite initialization."""

import os

# Disable background model refresh for all test runs to prevent unpatched network and filesystem access
os.environ["AGENT_OS_DISABLE_MODEL_REFRESH"] = "1"
