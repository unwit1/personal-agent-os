"""Skips for tests that exercise a specific host, with the reason spelled out.

They run in personal-agent-os CI, where the Agent OS host and checkout exist:
    ORCHESTRATOR_HOST=agent_os.orchestrator_host:HOST python -m unittest discover -s <orchestrator-os>/tests
"""

from __future__ import annotations

import os
import unittest

from orchestrator_os import host

AGENT_OS_HOST = os.environ.get(host.HOST_ENV, "").startswith("agent_os.")

requires_agent_os_host = unittest.skipUnless(
    AGENT_OS_HOST, "needs the Agent OS host (project registry, context compiler, work claims)")
requires_agent_os_checkout = unittest.skipUnless(
    AGENT_OS_HOST and host.LEGACY_LAYOUT,
    "asserts facts about the personal-agent-os repository itself (ORCHESTRATOR_STATE_ROOT=<personal-agent-os>)")
