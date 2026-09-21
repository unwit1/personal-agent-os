from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import workflows


def manifest(route: str, **extra) -> dict:
    stage = {
        "stage_id": "route-me", "goal": "Choose the cheapest declared route.",
        "required_context": {"task": "choose a route", "token_budget": 400, "include_handoff": False},
        "preferred_execution_path": "model", "capability_class": "fast", "effort": "low",
        "validator": {"kind": "outputs_present"}, "stop_condition": "a route is selected",
        "expected_outputs": ["result"], "next_stage": None,
    }
    stage.update(extra)
    return {"schema": workflows.MANIFEST_SCHEMA, "version": 1, "workflow_id": route,
            "project": "personal-agent-os", "goal": "P0.5 integration fixture.", "stages": [stage]}


class WorkflowExecutionPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "workflows").mkdir()
        (self.root / "projects" / "personal-agent-os" / "workflows").mkdir(parents=True)
        self.original_root, self.original_dir = workflows.ROOT, workflows.WORKFLOW_DIR
        workflows.ROOT, workflows.WORKFLOW_DIR = self.root, self.root / "workflows"

    def tearDown(self) -> None:
        workflows.ROOT, workflows.WORKFLOW_DIR = self.original_root, self.original_dir
        self.temp.cleanup()

    def write(self, data: dict) -> None:
        (workflows.WORKFLOW_DIR / f"{data['workflow_id']}.json").write_text(json.dumps(data), encoding="utf-8")

    def test_workflow_prepares_cache_route_before_model(self) -> None:
        (self.root / "cached.json").write_text("{}", encoding="utf-8")
        self.write(manifest("cache-first", cache={"path": "cached.json"}))
        workflows.start("cache-first", "cache-run")
        packet = workflows.run_stage("cache-first", "cache-run")
        self.assertEqual(packet["stage"]["execution"]["route"], "cache")
        self.assertIn("before any model escalation", packet["message"])
        self.assertEqual(workflows.load_run("personal-agent-os", "cache-run")["stages"]["route-me"]["execution"]["route"], "cache")

    def test_workflow_prepares_explicit_skill_before_model(self) -> None:
        self.write(manifest("skill-first", approved_skill="cheap-route-first"))
        workflows.start("skill-first", "skill-run")
        packet = workflows.run_stage("skill-first", "skill-run")
        self.assertEqual(packet["stage"]["execution"]["route"], "skill")
        self.assertEqual(packet["stage"]["execution"]["skill"]["name"], "cheap-route-first")


if __name__ == "__main__":
    unittest.main()
