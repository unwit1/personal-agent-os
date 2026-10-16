"""Keep Windows awake during work; all OS calls belong to one monitor thread."""
from __future__ import annotations

import ctypes
import sys
import threading
from contextlib import contextmanager
from typing import Any

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001


class KeepAwake:
    def __init__(self, enabled: bool = True, *, setter: Any = None, platform: str | None = None) -> None:
        self.enabled = enabled
        platform = platform or sys.platform
        self.setter = setter
        if self.setter is None and platform == "win32":
            self.setter = ctypes.windll.kernel32.SetThreadExecutionState
            self.setter.argtypes = [ctypes.c_uint]
            self.setter.restype = ctypes.c_uint
        self.held = False
        self._requests = 0
        self._lock = threading.Lock()
        self._changed = threading.Event()

    def configure(self, enabled: bool) -> None:
        with self._lock:
            self.enabled = enabled
        self._changed.set()

    @contextmanager
    def request(self):
        with self._lock:
            self._requests += 1
        self._changed.set()
        try:
            yield
        finally:
            with self._lock:
                self._requests -= 1
            self._changed.set()

    def update(self, active: bool = False) -> None:
        with self._lock:
            wanted = self.enabled and (active or self._requests > 0)
        if wanted != self.held:
            if self.setter:
                self.setter(ES_CONTINUOUS | (ES_SYSTEM_REQUIRED if wanted else 0))
            self.held = wanted

    def release(self) -> None:
        if self.held and self.setter:
            self.setter(ES_CONTINUOUS)
        self.held = False

    def monitor(self, stop: threading.Event, active: Any) -> None:
        try:
            while not stop.is_set():
                self._changed.clear()
                try:
                    working = bool(active())
                except Exception:
                    working = False
                self.update(working)
                self._changed.wait(0.5)
        finally:
            self.release()
