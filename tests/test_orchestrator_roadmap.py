"""Continue Roadmap, Auto Continue Until Done, and Simple Mode.

Integration tests run the real engine, Git worktrees, detected unit-test
validators and landing on a throwaway repository with a roadmap; model
workers are synthetic. UI state is tested through the Simple Mode view model
and the local HTTP API (plus the pure GUI helpers under Node when available).
"""

from __future__ import annotations

import http.client
import json
import re
import shutil
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_orchestrator import OrchestratorFixture  # noqa: E402

from agent_os.orchestrator import roadmap, service, simple  # noqa: E402
from agent_os.orchestrator.adapters import synthetic  # noqa: E402
from agent_os.orchestrator.server import build_server  # noqa: E402

ROADMAP = """# Test roadmap

## P0 — Base

### P0.1 — Done thing

Status: **complete** (2026-09-01).

### P0.2 — Second thing

Pending work for P0.2.

### P0.3 — Third thing

Pending work for P0.3.

### P0.4 — Parked thing

Status: **deferred** until later.
"""


def roadmap_script(request, call):
    """Planner plans the stage named in its prompt; the implementer marks it
    complete in the roadmap (as the real goal instructs); reviewers approve."""
    prompt = Path(request.prompt_path).read_text(encoding="utf-8")
    if request.role == "planner":
        stage = re.search(r"stage (P\d+\.\d+)", prompt).group(1)
        task = {"id": f"do-{stage.replace('.', '-').lower()}", "goal": f"complete {stage}", "scope": ["ROADMAP.md", "work"], "capability_class": "fast", "effort": "low"}
        return {"structured": {"status": "done", "tasks": [task]}}
    if request.role == "reviewer":
        return {"structured": {"status": "done", "verdict": "approved", "findings": []}}
    stage = re.search(r"complete (P\d+\.\d+)", prompt).group(1)
    text = (Path(request.cwd) / "ROADMAP.md").read_text(encoding="utf-8")
    return {
        "edits": {"ROADMAP.md": text.replace(f"Pending work for {stage}.", "Status: **complete** (test)."), f"work/{stage}.txt": "done\n"},
        "structured": {"status": "done"},
    }


class RoadmapParsingTests(unittest.TestCase):
    def test_classify_statuses(self) -> None:
        self.assertEqual(roadmap.classify("Status: **complete** (x)")[0], "complete")
        self.assertEqual(roadmap.classify("Status: **foundation complete**")[0], "partial")
        self.assertEqual(roadmap.classify("Status: **deferred** pending review")[0], "deferred")
        self.assertEqual(roadmap.classify("Status: **implemented, first release**")[0], "complete")
        self.assertEqual(roadmap.classify("text\nCurrent bounded implementation (2026): x")[0], "in_progress")
        self.assertEqual(roadmap.classify("no status here"), ("not_started", None))

    def test_parse_stages_in_order(self) -> None:
        stages = roadmap.parse(ROADMAP + "\n## P1 — Leaf section\n\nNothing yet.\n")
        self.assertEqual([stage["id"] for stage in stages], ["P0.1", "P0.2", "P0.3", "P0.4", "P1"])
        self.assertEqual([stage["status"] for stage in stages], ["complete", "not_started", "not_started", "deferred", "not_started"])
        self.assertEqual(stages[1]["title"], "Second thing")

    def test_choose_skips_complete_deferred_and_branches(self) -> None:
        stages = roadmap.parse(ROADMAP)
        stage, skipped = roadmap.choose_stage(stages, {})
        self.assertEqual(stage["id"], "P0.2")
        stage, skipped = roadmap.choose_stage(stages, {"P0.2": ["p0.2-other-agent"]})
        self.assertEqual(stage["id"], "P0.3")
        self.assertEqual(skipped[0]["stage"], "P0.2")
        self.assertIsNone(roadmap.choose_stage(stages, {}, skip={"P0.2", "P0.3"})[0])

    def test_goal_quotes_only_the_stage(self) -> None:
        stage = roadmap.parse(ROADMAP)[1]
        goal = roadmap.build_goal("demo", stage, "ROADMAP.md", {"remaining": ["finish the thing"]})
        self.assertIn("Pending work for P0.2.", goal)
        self.assertNotIn("P0.3", goal)
        self.assertIn("finish the thing", goal)
        self.assertLessEqual(len(goal), 4000)

    def test_real_project_roadmap_scans(self) -> None:
        from agent_os.paths import ROOT

        scanned = roadmap.scan("personal-agent-os", ROOT)
        self.assertTrue(scanned["found"])
        self.assertGreater(scanned["total"], 10)
        self.assertGreater(scanned["complete"], 0)
        self.assertTrue(any(stage["id"] == "P1.2A" for stage in scanned["stages"]))


class RoadmapFixture(OrchestratorFixture):
    def setUp(self) -> None:
        super().setUp()
        (self.repo / "ROADMAP.md").write_text(ROADMAP, encoding="utf-8")
        (self.repo / "tests").mkdir()
        (self.repo / "tests" / "test_ok.py").write_text("import unittest\n\nclass T(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-m", "roadmap")
        for name in self.providers:
            synthetic.SCRIPTS[name] = roadmap_script

    def cont(self, **kwargs):
        return roadmap.continue_roadmap(self.engine, None, self.repo, **kwargs)

    def types(self, run_id: str) -> list[str]:
        return [event["type"] for event in self.engine.ledger.read(run_id)[0]]


class ContinueRoadmapTests(RoadmapFixture):
    def test_continue_starts_earliest_stage_with_visible_steps(self) -> None:
        prep = roadmap.Preparation()
        seen: list[str] = []
        prep._on_change = lambda p: seen.append(p.message)
        result = self.cont(prep=prep)
        self.assertEqual(result["action"], "started")
        self.assertEqual(result["stage"]["id"], "P0.2")
        self.assertEqual([step["status"] for step in prep.view()["steps"]], ["done"] * 6)
        for message in ("Reading repository...", "Checking roadmap...", "Checking unfinished work...", "Loading previous handoff...", "Starting work..."):
            self.assertIn(message, seen)
        record = self.engine.load(result["run_id"])
        self.assertEqual(record["origin"]["stage_id"], "P0.2")
        self.assertEqual(record["policy"]["final_integration"], "merge_to_base")
        self.assertIn("discovered", record["policy"]["default_validators"][0]["name"])
        types = self.types(result["run_id"])
        for kind in ("run_started", "roadmap_scanned", "task_selected", "handoff_loaded", "context_selected", "local_execution"):
            self.assertIn(kind, types)

    def test_full_stage_runs_to_approval_then_lands(self) -> None:
        result = self.cont()
        final = self.engine.run_loop(result["run_id"], max_ticks=80)
        self.assertEqual(final["state"], "APPROVAL_REQUIRED")
        gate = next(gate for gate in final["gates"] if gate["status"] == "open")
        self.assertEqual(gate["kind"], "consequential_repository_write")
        view = simple.run_view(final, self.engine.ledger.read(result["run_id"])[0], self.engine.efficiency(result["run_id"]), [], driving=False)
        self.assertEqual(view["overall"], "NEEDS YOU")
        self.assertEqual(view["problems"][0]["recommended"]["label"], "Approve Commit")
        self.assertEqual(simple.advise({}, view)["message"], "Press Approve Commit. The work is finished and ready to save.")
        commit_step = next(step for step in view["steps"] if step["label"] == "Commit")
        self.assertEqual(commit_step["status"], "waiting")
        self.assertNotIn("Status: **complete** (test).", (self.repo / "ROADMAP.md").read_text(encoding="utf-8"), "nothing lands before approval")
        done = self.engine.decide(result["run_id"], gate["id"], True)
        self.assertEqual(done["state"], "COMPLETE")
        self.assertTrue(done["final"]["landed"]["ok"])
        self.assertIn("Status: **complete** (test).", (self.repo / "ROADMAP.md").read_text(encoding="utf-8"))
        self.assertEqual(roadmap.scan(None, self.repo)["complete"], 2)

    def test_unfinished_run_is_resumed_not_replanned(self) -> None:
        first = self.cont()
        self.engine.step(first["run_id"])  # planner launches
        self.engine.run_loop(first["run_id"], max_ticks=3)
        self.engine.pause(first["run_id"])
        second = self.cont()
        self.assertEqual(second["action"], "resumed")
        self.assertEqual(second["run_id"], first["run_id"])
        self.assertEqual(len(self.engine.list_runs()), 1, "no duplicate run")
        avoided = [event for event in self.engine.ledger.read(first["run_id"])[0] if event["type"] == "work_avoided"]
        self.assertEqual(avoided[-1]["data"]["category"], "resume")
        self.assertIsNone(avoided[-1]["data"]["tokens_avoided_estimate"], "synthetic planner cost is never used as an estimate")

    def test_waiting_run_needs_attention_and_fresh_sets_it_aside(self) -> None:
        first = self.cont()
        self.engine.run_loop(first["run_id"], max_ticks=80)
        self.assertEqual(self.cont()["action"], "needs_attention")
        fresh = self.cont(fresh=True)
        self.assertEqual(fresh["action"], "started")
        self.assertNotEqual(fresh["run_id"], first["run_id"])
        self.assertTrue(self.engine.load(first["run_id"])["origin"]["abandoned"])

    def test_nothing_to_do_avoids_a_model_call(self) -> None:
        (self.repo / "ROADMAP.md").write_text("# R\n\n## P0 — x\n\n### P0.1 — a\n\nStatus: **complete**.\n", encoding="utf-8")
        self.git("commit", "-am", "all done")
        result = self.cont()
        self.assertEqual(result["action"], "nothing_to_do")
        self.assertEqual(self.engine.list_runs(), [])

    def test_missing_roadmap_is_a_plain_error(self) -> None:
        (self.repo / "ROADMAP.md").unlink()
        self.git("commit", "-am", "no roadmap")
        result = self.cont()
        self.assertEqual(result["action"], "error")
        self.assertIn("could not find a roadmap", result["message"])

    def test_stage_with_foreign_branch_is_skipped(self) -> None:
        self.git("branch", "p0.2-someone-else")
        self.git("checkout", "p0.2-someone-else")
        (self.repo / "x.txt").write_text("x", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-m", "wip")
        self.git("checkout", "main")
        result = self.cont()
        self.assertEqual(result["stage"]["id"], "P0.3")
        guards = [event for event in self.engine.ledger.read(result["run_id"])[0] if event["type"] == "loop_guard"]
        self.assertEqual(guards[0]["data"]["guard"], "duplicate_roadmap_work")


class CampaignTests(RoadmapFixture):
    def test_auto_continue_until_done_walks_the_roadmap(self) -> None:
        first = self.cont(auto_until_done=True)
        key = self.repo.name
        campaign = roadmap.drive_campaign(self.engine, None, self.repo)
        self.assertEqual(campaign["status"], "waiting", "stops for the landing approval")
        for _ in range(3):
            current = roadmap.load_campaign(self.engine, key)["current_run"]
            status = self.engine.status(current)
            gate = next((gate for gate in status["gates"] if gate["status"] == "open"), None)
            if gate is None:
                break
            self.engine.decide(current, gate["id"], True)
            campaign = roadmap.drive_campaign(self.engine, None, self.repo)
        self.assertEqual(campaign["status"], "done")
        self.assertIn("Nothing to do", campaign["stop_reason"])
        stages = {stage["id"]: stage["status"] for stage in roadmap.scan(None, self.repo)["stages"]}
        self.assertEqual(stages, {"P0.1": "complete", "P0.2": "complete", "P0.3": "complete", "P0.4": "deferred"})
        runs = roadmap.load_campaign(self.engine, key)["runs"]
        self.assertEqual([item["stage_id"] for item in runs], ["P0.2", "P0.3"])
        self.assertEqual({item["outcome"] for item in runs}, {"COMPLETE"})
        self.assertEqual(runs[0]["run_id"], first["run_id"])

    def test_stage_that_never_completes_is_not_repeated_forever(self) -> None:
        def lazy(request, call):
            behaviour = roadmap_script(request, call)
            if request.role not in {"planner", "reviewer"}:
                behaviour["edits"] = {"work/x.txt": f"{call}\n"}  # never marks the stage complete
            return behaviour

        for name in self.providers:
            synthetic.SCRIPTS[name] = lazy
        self.cont(auto_until_done=True, policy={"final_integration": "branch"})
        campaign = roadmap.drive_campaign(self.engine, None, self.repo, max_runs=6, policy={"final_integration": "branch"})
        stages = [item["stage_id"] for item in campaign["runs"]]
        self.assertEqual(stages.count("P0.2"), roadmap.MAX_RUNS_PER_STAGE)
        self.assertEqual(stages.count("P0.3"), roadmap.MAX_RUNS_PER_STAGE)
        self.assertEqual(campaign["status"], "done", "stops when every eligible stage hit its limit")
        guards = {event["data"].get("guard") for item in campaign["runs"] for event in self.engine.ledger.read(item["run_id"])[0] if event["type"] == "loop_guard"}
        self.assertIn("stage_repeat", guards)


class SimpleViewTests(RoadmapFixture):
    def view(self, run_id: str, driving: bool = False):
        return simple.run_view(self.engine.status(run_id), self.engine.ledger.read(run_id)[0], self.engine.efficiency(run_id), [{"id": "alpha", "enabled": True, "probe": {"available": True}}, {"id": "beta", "enabled": True, "probe": {"available": True}}], driving=driving)

    def test_steps_progress_and_agents(self) -> None:
        run_id = self.cont()["run_id"]
        synthetic.SCRIPTS["alpha"] = synthetic.SCRIPTS["beta"] = lambda request, call: {**roadmap_script(request, call), "ticks": 2}
        self.engine.step(run_id)
        view = self.view(run_id, driving=True)
        self.assertEqual(view["overall"], "WORKING")
        self.assertEqual(view["steps"][0], {"label": "Plan", "status": "active", "detail": "alpha is planning"})
        working = [row for row in view["agents"] if row["status"] == "Planning"]
        self.assertEqual(len(working), 1)
        self.assertEqual(view["stage"], {"id": "P0.2", "title": "Second thing"})
        self.assertEqual(simple.advise({}, view)["message"], "Nothing needs your attention. alpha is still planning.")
        self.engine.run_loop(run_id, max_ticks=80)
        done = self.view(run_id)
        statuses = {step["label"]: step["status"] for step in done["steps"]}
        self.assertEqual(statuses["Plan"], "done")
        self.assertEqual(statuses["Implement"], "done")
        self.assertEqual(statuses["Test"], "done")
        self.assertEqual(statuses["Review"], "done")
        self.assertEqual(statuses["Commit"], "waiting")
        self.assertTrue(any("Review of" in item["text"] for item in done["activity"]))

    def test_paused_interrupted_and_failed_states(self) -> None:
        run_id = self.cont()["run_id"]
        self.engine.pause(run_id)
        view = self.view(run_id)
        self.assertEqual(view["overall"], "PAUSED")
        self.assertEqual(simple.advise({}, view)["target"], "resume")
        self.engine.resume(run_id)
        interrupted = self.view(run_id, driving=False)
        self.assertEqual(interrupted["overall"], "INTERRUPTED")
        self.assertEqual(simple.advise({}, interrupted)["message"], "Press Resume. The previous run was interrupted.")
        synthetic.SCRIPTS["alpha"] = synthetic.SCRIPTS["beta"] = lambda request, call: {"failure": "quota"}
        self.engine.run_loop(run_id, max_ticks=20)
        failed = self.view(run_id)
        self.assertEqual(failed["overall"], "STOPPED")
        card = failed["problems"][0]
        self.assertEqual(card["recommended"]["label"], "Try Again")
        self.assertIn("run out of usage", card["what"])
        self.assertIn("No other available agent", card["what"])
        self.assertNotIn("quota", card["title"] + card["what"], "raw error kinds stay in Advanced Details")
        self.assertIn("failures", card["advanced"])

    def test_every_gate_kind_has_a_friendly_card(self) -> None:
        from agent_os.orchestrator.model import APPROVAL_GATES

        for kind in APPROVAL_GATES:
            card = simple.gate_card({"id": "G1", "kind": kind, "reason": "raw technical reason", "node": None})
            self.assertNotIn("_", card["title"])
            self.assertTrue(card["changed"])
            self.assertIn(card["recommended"]["decision"], {"approve", "reject"})
            self.assertEqual(card["advanced"]["kind"], kind)

    def test_home_advice(self) -> None:
        self.assertEqual(simple.advise({"next_stage": {"id": "P0.2"}}, None)["message"], "Press Continue Roadmap. Everything is ready.")
        self.assertEqual(simple.advise({"next_stage": None, "roadmap": {"total": 1}}, None)["target"], None)
        self.assertEqual(simple.advise({"unfinished_runs": [{"state": "PAUSED"}]}, None)["target"], "continue")
        self.assertEqual(simple.advise({}, None, {"state": "running", "message": "Checking roadmap..."})["message"], "Nothing needs your attention. Checking roadmap...")
        unavailable = {"providers": [{"id": "x", "enabled": True, "probe": {"available": False}}]}
        self.assertEqual(simple.advise(unavailable, None)["target"], "settings")

    def test_default_view_is_compact(self) -> None:
        run_id = self.cont()["run_id"]
        self.engine.run_loop(run_id, max_ticks=80)
        view = self.view(run_id)
        self.assertLessEqual(len(view["steps"]), 7)
        self.assertLessEqual(len(view["problems"]), 3)
        text = json.dumps({key: view[key] for key in ("headline", "current_task", "steps", "problems")})
        for jargon in ("worktree", "node", "FAILED_FINAL", "consequential_repository_write"):
            self.assertNotIn(jargon, json.dumps({key: view[key] for key in ("headline", "current_task", "steps")}))
        self.assertIn("consequential_repository_write", text, "the raw kind is kept for Advanced Details")


class SimpleApiTests(RoadmapFixture):
    def setUp(self) -> None:
        super().setUp()
        service.set_engine(self.engine)
        self.addCleanup(service.set_engine, None)
        self.server, self.token = build_server("127.0.0.1", 0)
        self.server.api.default_project = None
        self.server.api.default_repository = str(self.repo)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def call(self, method: str, path: str, body: dict | None = None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        headers = {"Host": f"127.0.0.1:{self.port}", "X-Agent-OS-Token": self.token, "Content-Type": "application/json"}
        started = time.monotonic()
        connection.request(method, path, body=json.dumps(body) if body is not None else None, headers=headers)
        response = connection.getresponse()
        data = json.loads(response.read() or b"null")
        connection.close()
        return response.status, data, time.monotonic() - started

    def test_continue_returns_immediately_and_reports_each_step(self) -> None:
        real_scan = roadmap.scan

        def slow_scan(*args, **kwargs):
            time.sleep(1.5)  # a large repository
            return real_scan(*args, **kwargs)

        with mock.patch.object(roadmap, "scan", side_effect=slow_scan):
            status, data, elapsed = self.call("POST", "/api/roadmap/continue", {})
            self.assertEqual(status, 200)
            self.assertLess(elapsed, 0.5, "the button must be acknowledged at once")
            prep_id = data["prep"]["id"]
            self.assertEqual(data["prep"]["state"], "running")
            time.sleep(0.4)
            _, prep, _ = self.call("GET", f"/api/prep/{prep_id}")
            self.assertEqual(prep["message"], "Checking roadmap...")
            self.assertEqual([step["status"] for step in prep["steps"][:2]], ["done", "active"])
            self.assertTrue(roadmap.wait_for(lambda: self.call("GET", f"/api/prep/{prep_id}")[1]["state"] != "running", 20))
        _, prep, _ = self.call("GET", f"/api/prep/{prep_id}")
        self.assertEqual(prep["state"], "done", prep)
        run_id = prep["result"]["run_id"]
        reached = roadmap.wait_for(lambda: self.engine.status(run_id)["state"] == "APPROVAL_REQUIRED", 120)
        status = self.engine.status(run_id)
        self.assertTrue(reached, (status["state"], status["state_reason"], self.server.drivers.error(run_id), [(n["id"], n["state"], n["wait_reason"]) for n in status["nodes"]]))
        _, view, _ = self.call("GET", f"/api/runs/{run_id}/simple")
        self.assertEqual(view["overall"], "NEEDS YOU")
        self.assertEqual(view["advice"]["target"], "problem:G1")
        self.assertGreater(len(view["activity"]), 5)
        self.assertTrue(view["efficiency"]["rows"])
        _, home, _ = self.call("GET", "/api/home")
        self.assertEqual(home["current_run"]["run_id"], run_id)
        self.assertIn("Approve Commit", home["advice"]["message"])
        _, done, _ = self.call("POST", f"/api/runs/{run_id}/decide", {"gate_id": "G1", "approve": True})
        self.assertEqual(done["state"], "COMPLETE")
        _, final_view, _ = self.call("GET", f"/api/runs/{run_id}/simple")
        self.assertEqual(final_view["summary"]["title"], "ROADMAP RUN COMPLETE")
        self.assertIsNone(final_view["summary"]["tokens_used_exact"], "synthetic calls report no tokens: unknown, not zero")
        rows = {row["label"]: row["value"] for row in final_view["efficiency"]["rows"]}
        self.assertIsNone(rows["Input tokens (provider-reported)"])
        _, efficiency, _ = self.call("GET", f"/api/runs/{run_id}/efficiency")
        self.assertTrue(efficiency["reconciliation"]["consistent"])

    def test_home_fast_and_actions_on_idle(self) -> None:
        status, home, elapsed = self.call("GET", "/api/home")
        self.assertEqual(status, 200)
        self.assertLess(elapsed, 5)
        self.assertEqual(home["next_stage"]["id"], "P0.2")
        self.assertEqual(home["advice"]["target"], "continue")
        self.assertIsNone(home["current_run"])
        status, usage, _ = self.call("GET", "/api/usage")
        self.assertEqual(status, 200)
        rows = {row["label"]: row for row in usage["rows"]}
        self.assertEqual(rows["Model calls"]["value"], 0)
        self.assertIsNone(rows["Input tokens (provider-reported)"]["value"], "no reports: unknown, not zero")


class GuiCoreTests(unittest.TestCase):
    def test_simple_core_under_node(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed")
        test = Path(__file__).resolve().parent / "gui" / "simple_core.test.js"  # a file path: `--test <dir>` fails on Windows
        completed = subprocess.run([node, "--test", str(test)], capture_output=True, text=True, timeout=120)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
