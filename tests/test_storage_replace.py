"""FAIL-0005: atomic JSON writes survive a brief Windows sharing violation."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import storage  # noqa: E402


class ReplaceRetryTests(unittest.TestCase):
    def test_transient_permission_error_is_retried(self) -> None:
        real = storage.os.replace
        calls = {"n": 0}

        def flaky(source, target):
            calls["n"] += 1
            if calls["n"] < 3:
                raise PermissionError(5, "Access is denied")
            return real(source, target)

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(storage.os, "replace", side_effect=flaky), mock.patch.object(storage.time, "sleep"):
            path = Path(tmp) / "state.json"
            storage.write_json(path, {"ok": True})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"ok": True})
            self.assertEqual(calls["n"], 3)

    def test_persistent_error_propagates_and_cleans_the_temp_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(storage.os, "replace", side_effect=PermissionError(5, "denied")), mock.patch.object(storage.time, "sleep") as sleep:
            with self.assertRaises(PermissionError):
                storage.write_json(Path(tmp) / "state.json", {})
            self.assertEqual(sleep.call_count, 4)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_other_errors_are_not_retried(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(storage.os, "replace", side_effect=FileNotFoundError()) as replace:
            with self.assertRaises(FileNotFoundError):
                storage.write_json(Path(tmp) / "state.json", {})
            self.assertEqual(replace.call_count, 1)


if __name__ == "__main__":
    unittest.main()
