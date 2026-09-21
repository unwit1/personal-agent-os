"""Reentrant process/thread locks; OS releases the file lock after a crash."""
from __future__ import annotations

import os
import threading
import time
from contextlib import contextmanager
from functools import wraps

from .paths import ROOT

_mutex = threading.RLock()
_active: set[str] = set()


@contextmanager
def locked(name: str = "canonical", timeout: float = 15):
    # One in-process mutex also makes nested canonical/task locks reentrant.
    with _mutex:
        if name in _active:
            yield
            return
        directory = ROOT / ".agent-local" / "locks"
        directory.mkdir(parents=True, exist_ok=True)
        with (directory / f"{name}.lock").open("a+b") as handle:
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
            deadline = time.monotonic() + timeout
            while True:
                try:
                    handle.seek(0)
                    if os.name == "nt":
                        import msvcrt
                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError("Agent OS state is busy; retry the operation") from None
                    time.sleep(0.05)
            _active.add(name)
            try:
                yield
            finally:
                _active.remove(name)
                handle.seek(0)
                if os.name == "nt":
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle, fcntl.LOCK_UN)


def canonical_write(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        with locked():
            return function(*args, **kwargs)
    return wrapped
