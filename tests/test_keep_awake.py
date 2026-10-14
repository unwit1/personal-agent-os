from __future__ import annotations

import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from agent_os.executive.keep_awake import ES_CONTINUOUS, ES_SYSTEM_REQUIRED, KeepAwake


class KeepAwakeTests(unittest.TestCase):
    def test_windows_flags_release_and_no_repeated_calls(self):
        setter = Mock()
        wake = KeepAwake(setter=setter)
        wake.update(True)
        wake.update(True)
        setter.assert_called_once_with(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
        wake.update(False)
        self.assertEqual(setter.call_args.args, (ES_CONTINUOUS,))
        wake.release()
        self.assertEqual(setter.call_count, 2)

    def test_nested_requests_and_exception_release(self):
        wake = KeepAwake(setter=Mock())
        with self.assertRaises(RuntimeError):
            with wake.request():
                with wake.request():
                    wake.update()
                wake.update()
                self.assertTrue(wake.held)
                raise RuntimeError("request failed")
        wake.update()
        self.assertFalse(wake.held)

    def test_preference_turns_off_active_request(self):
        wake = KeepAwake(setter=Mock())
        with wake.request():
            wake.update()
            wake.configure(False)
            wake.update(True)
            self.assertFalse(wake.held)
            wake.configure(True)
            wake.update()
            self.assertTrue(wake.held)
        wake.release()

    def test_off_windows_is_noop(self):
        wake = KeepAwake(platform="linux")
        self.assertIsNone(wake.setter)
        wake.update(True)
        wake.release()

    def test_monitor_owns_all_os_calls_and_releases_on_exit(self):
        stop = threading.Event()
        acquired = threading.Event()
        calls = []
        def setter(flags):
            calls.append((flags, threading.get_ident()))
            if flags & ES_SYSTEM_REQUIRED:
                acquired.set()
        wake = KeepAwake(setter=setter)
        thread = threading.Thread(target=wake.monitor, args=(stop, lambda: True))
        thread.start()
        try:
            self.assertTrue(acquired.wait(2))
        finally:
            stop.set()
            wake._changed.set()
            thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual([flags for flags, _ in calls], [ES_CONTINUOUS | ES_SYSTEM_REQUIRED, ES_CONTINUOUS])
        self.assertEqual({owner for _, owner in calls}, {thread.ident})

    def test_monitor_handles_failed_probe(self):
        stop = threading.Event()
        def active():
            stop.set()
            raise RuntimeError("probe failed")
        wake = KeepAwake(platform="linux")
        wake.monitor(stop, active)
        self.assertFalse(wake.held)


if __name__ == "__main__":
    unittest.main()
