"""Loaded by Python in Codex worker commands on Windows (the adapter puts this
directory first on PYTHONPATH).

Python 3.13+ gives ``os.mkdir(path, 0o700)`` an owner-only ACL on Windows, and
``tempfile.mkdtemp`` / ``TemporaryDirectory`` create every folder that way.
Codex's restricted-token sandbox can create such a folder but not write into
it, so every test that uses a temporary directory fails with WinError 5. Here
tempfile alone creates its folders with the default ACL (inherited from the
user's temp directory); nothing else in the process is changed. Accepted by
the operator on 2026-09-30.
"""

import os
import sys

if os.name == "nt" and os.environ.get("AGENT_OS_ORCHESTRATOR_WORKER") == "1":
    import tempfile
    import types

    _mkdir = os.mkdir

    def _mkdir_inherited(path, mode=0o777, *, dir_fd=None):
        return _mkdir(path, 0o777 if mode == 0o700 else mode, dir_fd=dir_fd)

    _os = types.ModuleType("os")
    _os.__dict__.update(os.__dict__)
    _os.mkdir = _mkdir_inherited
    tempfile._os = _os


def _chain() -> None:
    """Run the sitecustomize this file shadows, if the environment has one."""
    import importlib

    here = os.path.dirname(os.path.abspath(__file__))
    saved = sys.path[:]
    module = sys.modules.pop("sitecustomize", None)
    try:
        sys.path[:] = [item for item in sys.path if os.path.abspath(item or ".") != here]
        importlib.import_module("sitecustomize")
    except ImportError:
        pass
    finally:
        sys.path[:] = saved
        if module is not None:
            sys.modules["sitecustomize"] = module


_chain()
