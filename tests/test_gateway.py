from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import shutil
import uuid
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, redirect_stdout
from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import candidates, changes, clients, gateway, handoffs, improvements, lifecycle, locking
from agent_os.cli import main
from agent_os.contracts import ENVELOPE, POSTFLIGHT, TRACE, validate_contract
from agent_os.mcp_server import _handle_mcp, methods
from agent_os.storage import load_json


def postflight(material=False):
    return {"summary": "Documented gateway behavior", "sanitized": True, "decisions": [],
            "evidence": ["tests/test_gateway.py"], "files_changed": ["README.md"] if material else [],
            "validation": {"status": "passed", "checks": ["Deterministic checks passed"]}, "remaining": []}


class GatewayTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[1] / ".tmp"
        scratch.mkdir(exist_ok=True)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = scratch / ("gateway-" + uuid.uuid4().hex)
        self.root.mkdir()
        def cleanup():
            if not self.root.resolve().is_relative_to(scratch.resolve()):
                raise ValueError("test cleanup escaped scratch directory")
            shutil.rmtree(self.root)
        self.stack.callback(cleanup)
        for module in (lifecycle, candidates, changes, improvements, handoffs, locking, clients):
            self.stack.enter_context(patch.object(module, "ROOT", self.root))

    def begin(self, project="personal-agent-os", query="Improve task lifecycle"):
        return lifecycle.begin_task(query, "test", project_hint=project)

    def canonical(self):
        return list((self.root / "projects").rglob("*.json"))

    def test_gateway_preflight_precedes_execution_and_postflight_follows(self):
        class Worker:
            def execute(_, request):
                task = lifecycle.task_status(request["envelope"]["task_id"])
                self.assertEqual(task["status"], "active")
                self.assertTrue(task["preflight_completed"])
                self.assertEqual(request["request"], "Suggest dinner")
                return {"response": "Soup", "postflight": postflight()}
        result = gateway.run("Suggest dinner", Worker())
        self.assertEqual(result["response"], "Soup")
        self.assertEqual(lifecycle.task_status(result["task_id"])["status"], "finished")
        self.assertEqual(result["exit_code"], 0)
        self.assertFalse(self.canonical())

    def test_preflight_failure_never_executes_worker(self):
        worker = Mock()
        with patch.object(lifecycle, "_retrieve", side_effect=RuntimeError("private source")):
            with self.assertRaises(lifecycle.PreflightError):
                gateway.run("Do work", worker)
        worker.execute.assert_not_called()
        journal = load_json(next((self.root / ".agent-local/tasks").glob("*.json")))
        self.assertEqual(journal["status"], "aborted")
        self.assertNotIn("private source", json.dumps(journal))

    def test_worker_failure_and_interruption_abort_without_private_exception(self):
        for error in (RuntimeError("secret private error"), KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__):
                worker = Mock()
                worker.execute.side_effect = error
                with self.assertRaises(gateway.GatewayError) as caught:
                    gateway.run("Suggest dinner", worker)
                task = lifecycle.task_status(caught.exception.task_id)
                self.assertEqual(task["status"], "aborted")
                self.assertNotIn("secret private error", json.dumps(task))

    def test_client_exit_status_is_preserved(self):
        worker = Mock()
        worker.execute.side_effect = clients.ClientFailure(7)
        with self.assertRaises(gateway.GatewayError) as caught:
            gateway.run("Suggest dinner", worker)
        self.assertEqual(caught.exception.exit_code, 7)

    def test_malformed_worker_result_is_not_success(self):
        worker = Mock()
        worker.execute.return_value = {"response": "done"}
        with self.assertRaises(gateway.GatewayError) as caught:
            gateway.run("Suggest dinner", worker)
        self.assertEqual(lifecycle.task_status(caught.exception.task_id)["status"], "aborted")

    def test_ordinary_prompt_loads_no_project(self):
        with patch.object(lifecycle, "search") as search:
            result = lifecycle.begin_task("What should I have for dinner?", "test")
        self.assertIsNone(result["routing"]["project"])
        self.assertEqual(result["context"], {})
        search.assert_not_called()

    def test_hr_gui_routing_budget_and_boundaries(self):
        for budget in (800, 1200, 2200):
            result = lifecycle.begin_task("Improve the form fingerprint matching behavior in HR-GUI.", "test", token_budget=budget)
            self.assertEqual(result["routing"]["project"], "hr-gui")
            self.assertFalse(result["privacy"]["raw_history_loaded"])
            self.assertFalse(result["privacy"]["prompt_persisted"])
            self.assertLessEqual((len(json.dumps(result, ensure_ascii=False)) + 3) // 4, budget)
            self.assertIn("privacy_boundary", result["context"])
            validate_contract(result, ENVELOPE)

    def test_ambiguous_routing_does_not_load_project_context(self):
        with patch("agent_os.chat.resolve_project", return_value={"project": {"id": "personal-agent-os"}, "confidence": "inferred", "ambiguous": True}), patch("agent_os.chat.compile_context") as compile_context:
            result = lifecycle.begin_task("Improve project workflow", "test")
        self.assertTrue(result["routing"]["ambiguous"])
        self.assertIsNone(result["routing"]["project"])
        compile_context.assert_not_called()

    def test_raw_input_session_and_metadata_are_never_persisted(self):
        private = "Review person@example.com with private payroll values"
        result = lifecycle.begin_task(private, "test", "private-session-value", execution_metadata={"source_text": "private document"})
        record = lifecycle.task_status(result["task_id"])
        serialized = json.dumps(record)
        self.assertNotIn(private, serialized)
        self.assertNotIn("private-session-value", serialized)
        self.assertNotIn("private document", serialized)
        self.assertEqual(record["privacy_classification"], "sensitive")
        self.assertFalse(self.canonical())

    def test_privacy_gate_prevents_all_canonical_postflight_writes(self):
        task = self.begin()
        payload = postflight(True)
        payload["summary"] = "Contact person@example.com"
        with self.assertRaises(ValueError):
            lifecycle.finish_task(task["task_id"], payload)
        self.assertFalse(self.canonical())
        self.assertEqual(lifecycle.task_status(task["task_id"])["status"], "active")
        payload["sanitized"] = False
        result = lifecycle.finish_task(task["task_id"], payload)
        self.assertFalse(result["durable_capture"])
        self.assertNotIn("person@example.com", json.dumps(lifecycle.task_status(task["task_id"])))

    def test_raw_source_and_hidden_reasoning_fields_are_rejected(self):
        for key in ("source_text", "raw_prompt", "chain_of_thought"):
            payload = postflight(True)
            payload[key] = "must never be stored"
            with self.assertRaises(ValueError):
                lifecycle.finish_task(self.begin()["task_id"], payload)
        self.assertFalse(self.canonical())

    def test_concurrent_task_ids_are_unique(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            ids = list(pool.map(lambda _: lifecycle.begin_task("Suggest dinner", "test")["task_id"], range(32)))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(list((self.root / ".agent-local/tasks").glob("*.json"))), 32)

    def test_continue_returns_deltas_and_reset_reloads(self):
        routed = {"project": "personal-agent-os", "resolution": {"confidence": "explicit"}}
        fixed = {"project": {"summary": "Compact context"}, "policy": {"canonical": "policy/CANONICAL_AGENT_POLICY.md"}}
        with patch.object(lifecycle, "_retrieve", return_value=(routed, fixed)):
            task = self.begin()
            delta = lifecycle.continue_task(task["task_id"], "A new request")
            self.assertEqual(delta["context"], {})
            full = lifecycle.continue_task(task["task_id"], "Continue", reset_context=True)
            self.assertEqual(full["context"], fixed)
        self.assertEqual(lifecycle.task_status(task["task_id"])["turn_count"], 3)

    def test_repeated_unchanged_turn_does_not_recompile(self):
        task = lifecycle.begin_task("Suggest dinner", "test")
        with patch.object(lifecycle, "_retrieve") as retrieve:
            result = lifecycle.continue_task(task["task_id"], "Suggest dinner")
        retrieve.assert_not_called()
        self.assertEqual(result["context"], {})

    def test_abort_resume_and_terminal_transitions(self):
        task = self.begin()
        lifecycle.abort_task(task["task_id"])
        with self.assertRaises(ValueError):
            lifecycle.continue_task(task["task_id"], "Continue")
        lifecycle.continue_task(task["task_id"], "Continue", resume=True)
        payload = postflight()
        first = lifecycle.finish_task(task["task_id"], payload)
        self.assertEqual(lifecycle.finish_task(task["task_id"], payload), first)
        with self.assertRaises(ValueError):
            lifecycle.abort_task(task["task_id"])
        with self.assertRaises(ValueError):
            lifecycle.continue_task(task["task_id"], "Continue")

    def test_material_capture_handoff_provenance_and_deduplication(self):
        payload = postflight(True)
        payload["decisions"] = [{"decision": "Keep context compact", "rationale_summary": "Reduce repeated loading"}]
        payload["proposed_improvements"] = [{"title": "Use negative anchors", "category": "performance",
            "observation": "Fingerprint matches can overlap", "suggested_direction": "Score negative anchors",
            "acceptance": ["Reject contradictory matches"], "evidence": ["tests/test_gateway.py"]}]
        ids = []
        for _ in range(2):
            task = self.begin()
            ids.append(task["task_id"])
            result = lifecycle.finish_task(task["task_id"], payload)
            self.assertTrue(result["durable_capture"])
            handoff = load_json(self.root / result["artifacts"]["handoff"])
            self.assertEqual(handoff["task_id"], task["task_id"])
            trace = load_json(self.root / result["artifacts"]["trace"])
            validate_contract(trace, TRACE)
            self.assertEqual(trace["status"], "unverified")
        change = changes.list_changes("personal-agent-os")
        improvement = improvements.list_improvements("personal-agent-os")
        self.assertEqual(len(change), 1)
        self.assertEqual(len(improvement), 1)
        self.assertEqual(change[0]["task_ids"], ids)
        self.assertEqual(improvement[0]["task_ids"], ids)
        candidate = candidates.candidate_status("personal-agent-os")["candidates"][0]
        self.assertEqual(candidate["task_ids"], ids)
        promoted = candidates.curate_candidates("personal-agent-os", [candidate["id"]], "promote")
        self.assertEqual(promoted["results"][0]["outcome"], "review_required")

    def test_partial_postflight_is_recoverable_without_duplicate_artifacts(self):
        task = self.begin()
        payload = postflight(True)
        with patch.object(lifecycle, "create_handoff", side_effect=OSError("private failure")):
            with self.assertRaises(OSError):
                lifecycle.finish_task(task["task_id"], payload)
        state = lifecycle.task_status(task["task_id"])
        self.assertEqual(state["status"], "postflight_pending")
        self.assertEqual(state["pending_postflight"], payload)
        self.assertEqual(len(changes.list_changes("personal-agent-os")), 1)
        lifecycle.abort_task(task["task_id"], stage="postflight", error_class="postflight_failed")
        different = deepcopy(payload)
        different["summary"] = "Different summary"
        with self.assertRaises(ValueError):
            lifecycle.finish_task(task["task_id"], different)
        result = lifecycle.finish_task(task["task_id"], payload)
        lifecycle.finish_task(task["task_id"], payload)
        self.assertEqual(result["status"], "finished")
        self.assertEqual(len(changes.list_changes("personal-agent-os")), 1)
        self.assertEqual(len(list((self.root / "projects/personal-agent-os/handoffs").glob("*.json"))), 1)

    def test_invalid_proposals_cannot_leave_partial_records(self):
        task = self.begin()
        payload = postflight(True)
        payload["proposed_improvements"] = [{"title": "", "category": "performance", "observation": "Overlap",
            "suggested_direction": "Score anchors", "acceptance": [], "evidence": ["test"]}]
        with self.assertRaises(ValueError):
            lifecycle.finish_task(task["task_id"], payload)
        self.assertFalse(self.canonical())
        self.assertEqual(lifecycle.task_status(task["task_id"])["status"], "active")

    def test_review_unavailable_is_honest_and_routine_work_does_not_call_reviewer(self):
        payload = postflight(True)
        payload["files_changed"] = ["policy/CANONICAL_AGENT_POLICY.md"]
        result = lifecycle.finish_task(self.begin()["task_id"], payload)
        self.assertEqual(result["outcome"], "review_required")
        self.assertEqual(result["review"]["status"], "unavailable")
        reviewer = Mock()
        lifecycle.finish_task(self.begin()["task_id"], postflight(), reviewer=reviewer)
        reviewer.assert_not_called()

    def test_independent_review_hook_is_validated_and_journaled(self):
        payload = postflight(True)
        payload["architecture_change"] = True
        for status in ("pass", "changes_requested"):
            reviewer = Mock(return_value={"status": status, "findings": []})
            task = self.begin()
            result = lifecycle.finish_task(task["task_id"], payload, reviewer=reviewer)
            lifecycle.finish_task(task["task_id"], payload, reviewer=reviewer)
            reviewer.assert_called_once()
            self.assertEqual(result["outcome"], "completed" if status == "pass" else "review_required")
        reviewer = Mock(side_effect=RuntimeError("private exception"))
        result = lifecycle.finish_task(self.begin()["task_id"], payload, reviewer=reviewer)
        self.assertEqual(result["review"]["status"], "failed")
        self.assertNotIn("private exception", json.dumps(result))

    def test_failed_validation_never_returns_success(self):
        worker = Mock()
        payload = postflight()
        payload["validation"]["status"] = "failed"
        worker.execute.return_value = {"response": "Work needs repair", "postflight": payload}
        result = gateway.run("Suggest dinner", worker)
        self.assertEqual(result["exit_code"], 3)
        self.assertEqual(result["postflight"]["outcome"], "validation_failed")

    def test_mcp_lifecycle_end_to_end(self):
        available = methods()
        def call(name, arguments):
            response = _handle_mcp({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments}}, available)["result"]
            self.assertFalse(response["isError"], response)
            return json.loads(response["content"][0]["text"])
        initialized = _handle_mcp({"id": 1, "method": "initialize"}, available)
        self.assertIn("agent.begin_task -> work -> agent.finish_task", initialized["result"]["instructions"])
        task = call("agent.begin_task", {"query": "Suggest dinner", "source_client": "mcp-test"})
        call("agent.continue_task", {"task_id": task["task_id"], "query": "Make it vegetarian"})
        call("agent.finish_task", {"task_id": task["task_id"], "postflight": postflight()})
        another = call("agent.begin_task", {"query": "Suggest dinner", "source_client": "mcp-test"})
        self.assertEqual(call("agent.abort_task", {"task_id": another["task_id"]})["status"], "aborted")

    def test_cli_lifecycle_smoke(self):
        output = io.StringIO()
        with patch("sys.stdin", io.StringIO("Suggest dinner")), redirect_stdout(output):
            self.assertEqual(main(["begin-task"]), 0)
        task_id = json.loads(output.getvalue())["task_id"]
        with patch("sys.stdin", io.StringIO(json.dumps(postflight()))), redirect_stdout(io.StringIO()):
            self.assertEqual(main(["finish-task", task_id, "--json", "-"]), 0)

    def test_command_worker_receives_request_over_stdin(self):
        code = "import json,sys; x=json.load(sys.stdin); print(json.dumps({'response': x['request'], 'postflight': " + repr(postflight()) + "}))"
        # Python booleans are valid in this Python program, not hand-built shell text.
        result = gateway.run("literal $() ; request", clients.CommandProvider([sys.executable, "-c", code]))
        self.assertEqual(result["response"], "literal $() ; request")

    def test_codex_wrapper_uses_ephemeral_structured_output_and_cleans_transit(self):
        def invoke(argv, packet, cwd, timeout):
            self.assertIn("--ephemeral", argv)
            self.assertEqual(argv[-1], "-")
            self.assertNotIn("danger-full-access", argv)
            Path(argv[argv.index("--output-last-message") + 1]).write_text(json.dumps({"response": "done", "postflight": postflight()}))
            return "events"
        with patch.object(clients, "_executable", return_value=["codex.exe"]), patch.object(clients, "_invoke", side_effect=invoke), patch.object(clients, "transit_directory", side_effect=self.transit):
            gateway.run("Suggest dinner", clients.CLIProvider("codex"))
        self.assertEqual(list((self.root / ".agent-local/client-transit").iterdir()), [])

    def test_claude_wrapper_requires_structured_success(self):
        with patch.object(clients, "_executable", return_value=["claude.exe"]), patch.object(clients, "_invoke", return_value=json.dumps({"is_error": True, "structured_output": {}})), patch.object(clients, "transit_directory", side_effect=self.transit):
            with self.assertRaises(gateway.GatewayError):
                gateway.run("Suggest dinner", clients.CLIProvider("claude"))

    def transit(self, directory):
        # Inherit the sandbox ACL; Python 3.14's private tempfile ACL excludes it.
        from contextlib import contextmanager
        @contextmanager
        def fixture():
            path = directory / uuid.uuid4().hex
            path.mkdir()
            try:
                yield path
            finally:
                if not path.resolve().is_relative_to(self.root.resolve()):
                    raise ValueError("test cleanup escaped root")
                shutil.rmtree(path)
        return fixture()

    def test_task_path_traversal_is_rejected(self):
        for invalid in ("../../private", "TASK-../other", "TASK-" + "a" * 32 + "/other"):
            with self.assertRaises(ValueError):
                lifecycle.task_status(invalid)

    def test_parallel_capture_does_not_collide_improvement_ids(self):
        def capture(index):
            return improvements.capture_improvement("personal-agent-os", "Improvement " + str(index), "performance",
                "Reduce repeated context", "Cache selective metadata", ["Return compact context"], evidence=["test"])["record"]["id"]
        with ThreadPoolExecutor(max_workers=6) as pool:
            ids = list(pool.map(capture, range(12)))
        self.assertEqual(len(set(ids)), 12)
        self.assertEqual(len(improvements.list_improvements("personal-agent-os")), 12)

    def test_process_capture_lock_preserves_unique_ids(self):
        src = str(Path(__file__).resolve().parents[1] / "src")
        code = "import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); from agent_os import improvements,locking; improvements.ROOT=locking.ROOT=Path(sys.argv[2]); result=improvements.capture_improvement('personal-agent-os',sys.argv[3],'performance','Reduce redundant context','Cache metadata',['Compact response']); print(result['record']['id'])"
        children = [subprocess.Popen([sys.executable, "-c", code, src, str(self.root), f"Suggestion {number}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for number in range(6)]
        ids = []
        for child in children:
            stdout, stderr = child.communicate(timeout=20)
            self.assertEqual(child.returncode, 0, stderr)
            ids.append(stdout.strip())
        self.assertEqual(len(set(ids)), 6)
        self.assertEqual(len(improvements.list_improvements("personal-agent-os")), 6)

    def test_timeout_records_abort_and_stops_worker(self):
        worker = clients.CommandProvider([sys.executable, "-c", "import time; time.sleep(15)"], timeout=0.1)
        with self.assertRaises(gateway.GatewayError) as caught:
            gateway.run("Suggest dinner", worker)
        task = lifecycle.task_status(caught.exception.task_id)
        self.assertEqual(task["failure"]["error_class"], "timeout")

    def test_claude_wrapper_success_extracts_structured_output(self):
        output = {"response": "done", "postflight": postflight()}
        with patch.object(clients, "_executable", return_value=["claude.exe"]), patch.object(clients, "_invoke", return_value=json.dumps({"structured_output": output})) as invoke, patch.object(clients, "transit_directory", side_effect=self.transit):
            result = gateway.run("Suggest dinner", clients.CLIProvider("claude"))
        self.assertEqual(result["response"], "done")
        argv = invoke.call_args.args[0]
        self.assertIn("--no-session-persistence", argv)
        self.assertIn("--json-schema", argv)

    def test_missing_client_aborts(self):
        with patch.object(clients.shutil, "which", return_value=None):
            with self.assertRaises(gateway.GatewayError) as caught:
                gateway.run("Suggest dinner", clients.CLIProvider("claude"))
        self.assertEqual(caught.exception.exit_code, 127)
        self.assertEqual(lifecycle.task_status(caught.exception.task_id)["status"], "aborted")


if __name__ == "__main__":
    unittest.main()
