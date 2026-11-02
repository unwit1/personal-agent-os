"""pytest plugin loaded in Codex worker commands on Windows (the adapter names
it in PYTEST_PLUGINS; this directory is first on PYTHONPATH).

pytest's ``tmp_path`` factory creates its base and per-test folders with
``Path.mkdir(mode=0o700)``. On Python 3.13+ that gives them an owner-only
ACL, which Codex's restricted-token sandbox can create but not write into --
the same failure sitecustomize.py fixes for ``tempfile``. Here, only while
the temp-path factory is making a folder, 0o700 becomes the default mode
(ACL inherited from the user's temp directory); nothing else is changed.
"""

import functools
import os
import pathlib

_ACTIVE = os.name == "nt" and os.environ.get("AGENT_OS_ORCHESTRATOR_WORKER") == "1"


def _inherited(method):
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        original = pathlib.Path.mkdir

        def mkdir(self, mode=0o777, parents=False, exist_ok=False):
            return original(self, 0o777 if mode == 0o700 else mode, parents, exist_ok)

        pathlib.Path.mkdir = mkdir
        try:
            return method(*args, **kwargs)
        finally:
            pathlib.Path.mkdir = original

    wrapper.agent_os_inherited_acl = True
    return wrapper


def pytest_configure(config):
    if not _ACTIVE:
        return
    from _pytest.tmpdir import TempPathFactory

    for name in ("getbasetemp", "mktemp"):
        method = getattr(TempPathFactory, name)
        if not getattr(method, "agent_os_inherited_acl", False):
            setattr(TempPathFactory, name, _inherited(method))
