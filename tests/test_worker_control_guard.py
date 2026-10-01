import os
import unittest
from unittest import mock

from agent_os.orchestrator import service


class WorkerControlGuardTests(unittest.TestCase):
    def tearDown(self) -> None:
        service.set_engine(None)

    def test_worker_cannot_control_the_machines_default_engine(self) -> None:
        service.set_engine(None)  # nothing embedded: control would reach the shared default engine
        with mock.patch.dict(os.environ, {service.WORKER_MARKER: "1"}):
            with self.assertRaises(RuntimeError):
                service.step("run-x")

    def test_worker_may_drive_an_embedded_engine(self) -> None:
        # A worker running the test suite: fixtures embed their own engine.
        embedded = mock.Mock()
        embedded.step.return_value = {"run_id": "run-x"}
        service.set_engine(embedded)
        with mock.patch.dict(os.environ, {service.WORKER_MARKER: "1"}):
            service.step("run-x")
        embedded.step.assert_called_once()


if __name__ == "__main__":
    unittest.main()
