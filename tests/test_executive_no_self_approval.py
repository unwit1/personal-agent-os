"""The chat model cannot approve its own consequential actions.

executive.approve, executive.send with confirm_send=true, and browser.execute with
approved_consequential=true only leave a pending record for the window; the
confirm token never reaches the model, and only Registry.confirm (the window's
Confirm click) performs the side effect.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import browser_control, mcp_server
from agent_os.executive import applicants as ex
from agent_os.executive.window import actions_executive, registry
from agent_os.executive.window.confirm import ENV_HOME, PendingStore

FUTURE = datetime.now().replace(microsecond=0) + timedelta(days=3)
ROWS = [{"agent_ref": "ref-a", "name": "Ann", "position": "Tech", "submitted": "2026-09-20",
         "status": "New", "county": "Kent", "city": "Dover"}]
CLICK = [{"op": "click", "selector": "button[type=submit]"}]


class MemStore:
    def __init__(self):
        self.data = {}

    def save(self, batch):
        self.data[batch["batch_id"]] = json.loads(json.dumps(batch))

    def load(self, batch_id):
        return json.loads(json.dumps(self.data[batch_id]))


class FakeGateway:
    def __init__(self):
        self.calls = []

    def match_for(self, ref):
        return {"match": "Tech", "pending": False, "alternates": [], "reasons": []}

    def manager_for(self, ref):
        return "Mgr"

    def suggest_slots(self, manager, duration_minutes, count):
        return [(FUTURE, "free")]

    def render_outreach(self, name, position, slots, interview_type, location, duration_minutes, message, county):
        return f"Interview: {position}", f"Hello {name}"

    def record_outreach_drafted(self, ref, slots, interview_type, location, duration_minutes, draft_path, area_manager):
        self.calls.append(("draft", ref))
        return "draft-1"

    def send_now(self, ref, kind, to_addr, subject, body):
        self.calls.append(("send_now", ref))
        return "email-1"

    def sends(self):
        return [c[1] for c in self.calls if c[0] == "send_now"]


def call(name, **arguments):
    request = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments}}
    result = mcp_server._handle_mcp(request, mcp_server.methods())["result"]
    return bool(result.get("isError")), json.loads(result["content"][0]["text"])


class NoSelfApprovalTests(unittest.TestCase):
    def setUp(self):
        self.gw, self.store = FakeGateway(), MemStore()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = tmp.name
        patches = (
            patch.dict(os.environ, {ENV_HOME: self.home}),
            patch.object(mcp_server, "_executive_gateway", lambda: self.gw),
            patch.object(mcp_server, "_executive_store", lambda: self.store),
            patch.object(actions_executive, "GATEWAY_FACTORY", lambda: self.gw),
            patch.object(actions_executive, "STORE_FACTORY", lambda: self.store),
            patch.object(ex.rtec_applicants, "list_applicants",
                         side_effect=lambda status=None, limit=50, offset=0: {"count": 1, "results": [dict(r) for r in ROWS]}),
            patch.object(ex.rtec_applicants, "get_summary", side_effect=lambda ref: {"applicant_ref": ref, "email": "ann@example.test"}),
            patch.object(ex.rtec_applicants, "_audit_access", lambda *a, **k: None),
        )
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.pending = PendingStore(self.home)
        self.reg = registry.Registry()
        actions_executive.register(self.reg)

    def plan(self):
        batch = ex.plan_outreach(["ref-a"], "Tech", "phone", "HQ", 30, gateway=self.gw, store=self.store)
        return batch["batch_id"]

    def approved(self):
        batch_id = self.plan()
        ex.approve_batch(batch_id, {"ref-a": "confirm"}, gateway=self.gw, store=self.store)
        return batch_id

    def assert_parked(self, out, action_id):
        """needs_confirmation, no token anywhere in the reply, exactly one pending record."""
        self.assertEqual(out["status"], "needs_confirmation")
        self.assertIs(out["confirm_token_issued"], True)
        self.assertIn("Confirm", out["message"])
        self.assertNotIn("confirm_token", out)
        records = self.pending.list()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["action_id"], action_id)
        self.assertNotIn(records[0]["token"], json.dumps(out))
        return records[0]

    def test_send_with_confirm_send_does_not_send(self):
        batch_id = self.approved()
        with patch.object(ex, "_send_item", wraps=ex._send_item) as send_item:
            err, out = call("executive.send", batch_id=batch_id, confirm_send=True)
            self.assertFalse(err, out)
            send_item.assert_not_called()
        self.assertEqual(self.gw.sends(), [])
        self.assertEqual(self.store.load(batch_id)["state"], ex.APPROVED)
        record = self.assert_parked(out, "executive.send_batch")
        self.assertEqual(record["params"], {"batch_id": batch_id})

        result = self.reg.confirm(record["token"], self.pending)
        self.assertEqual(result["sent"], ["ref-a"])
        self.assertEqual(self.gw.sends(), ["ref-a"])
        self.assertEqual(self.pending.list(), [])
        with self.assertRaises(KeyError):
            self.reg.confirm(record["token"], self.pending)
        self.assertEqual(self.gw.sends(), ["ref-a"])

    def test_send_preview_is_unchanged(self):
        batch_id = self.approved()
        err, out = call("executive.send", batch_id=batch_id)
        self.assertFalse(err, out)
        self.assertTrue(out["dry_run"])
        self.assertEqual(self.pending.list(), [])
        self.assertEqual(self.gw.sends(), [])

    def test_approve_does_not_approve(self):
        batch_id = self.plan()
        with patch.object(ex, "approve_batch", wraps=ex.approve_batch) as approve:
            err, out = call("executive.approve", batch_id=batch_id, choices={"ref-a": "confirm"})
            self.assertFalse(err, out)
            approve.assert_not_called()
        self.assertEqual(self.store.load(batch_id)["state"], ex.PENDING_APPROVAL)
        record = self.assert_parked(out, "executive.approve_batch")

        with patch.object(ex, "approve_batch", wraps=ex.approve_batch) as approve:
            result = self.reg.confirm(record["token"], self.pending)
            self.assertEqual(approve.call_count, 1)
        self.assertEqual(result["state"], ex.APPROVED)
        self.assertEqual(self.store.load(batch_id)["state"], ex.APPROVED)
        self.assertEqual(self.gw.sends(), [])  # approval never sends

    def test_browser_execute_approved_does_not_execute(self):
        with patch.object(mcp_server, "browser_execute") as preview_path, \
                patch.object(browser_control, "execute", return_value={"state": "completed"}) as execute:
            err, out = call("browser.execute", session_id="s-1", actions=CLICK, approved_consequential=True)
            self.assertFalse(err, out)
            preview_path.assert_not_called()
            execute.assert_not_called()
            record = self.assert_parked(out, "browser.execute_consequential")

            result = self.reg.confirm(record["token"], self.pending)
            self.assertEqual(result, {"state": "completed"})
            execute.assert_called_once()
            args, kwargs = execute.call_args
            self.assertEqual(args, ("s-1", CLICK))
            self.assertIs(kwargs["approved_consequential"], True)
            preview_path.assert_not_called()

    def test_browser_execute_unapproved_keeps_working(self):
        with patch.object(mcp_server, "browser_execute", return_value={"state": "approval_required"}) as execute:
            err, out = call("browser.execute", session_id="s-1", actions=CLICK)
            self.assertFalse(err, out)
        self.assertEqual(out, {"state": "approval_required"})
        execute.assert_called_once()
        self.assertNotIn("approved_consequential", execute.call_args.kwargs)
        self.assertEqual(self.pending.list(), [])

    def routine_run(self, approve):
        """A browser routine paused on CLICK; approve=True is the window's Confirm (approve_run)."""
        from agent_os import browser_routines
        from agent_os.browser_bridge import BridgeStore

        home = Path(self.home) / "routines"
        policy_path = browser_routines._home(home) / "policies" / "run-1.json"
        policy_path.write_text(json.dumps({"issuer": "routine:run-1", "session_ids": ["tab-1"], "approved_hashes": []}))
        browser_routines.save_run({
            "run_id": "run-1", "status": "needs_approval", "policy": str(policy_path),
            "pending_approval": {"actions": CLICK, "actions_hash": BridgeStore.actions_hash(CLICK)},
        }, home)
        if approve:
            browser_routines.approve_run("run-1", home)
        env = getattr(browser_control, "POLICY_ENV", "AGENT_OS_BROWSER_POLICY")
        return policy_path, patch.dict(os.environ, {env: str(policy_path)})

    def test_routine_resume_runs_the_operator_approved_action_once(self):
        """After the window approval, the resumed routine's re-issued call executes (once)."""
        policy_path, env = self.routine_run(approve=True)
        with env, patch.object(mcp_server, "browser_execute", return_value={"state": "completed"}) as execute:
            err, out = call("browser.execute", session_id="tab-1", actions=CLICK, approved_consequential=True)
            self.assertFalse(err, out)
            self.assertEqual(out, {"state": "completed"})
            execute.assert_called_once()
            self.assertEqual(execute.call_args.args, ("tab-1", CLICK))
            self.assertIs(execute.call_args.kwargs["approved_consequential"], True)
            self.assertEqual(execute.call_args.kwargs["issued_by"], "routine:run-1")
            self.assertEqual(self.pending.list(), [])
            self.assertEqual(json.loads(policy_path.read_text())["approved_hashes"], [])

            err, out = call("browser.execute", session_id="tab-1", actions=CLICK, approved_consequential=True)
            self.assertEqual(execute.call_count, 1)  # the approval is single-use
            self.assert_parked(out, "browser.execute_consequential")

    def test_routine_without_operator_approval_cannot_self_approve(self):
        _, env = self.routine_run(approve=False)
        with env, patch.object(mcp_server, "browser_execute") as execute:
            err, out = call("browser.execute", session_id="tab-1", actions=CLICK, approved_consequential=True)
            self.assertFalse(err, out)
            execute.assert_not_called()
            self.assert_parked(out, "browser.execute_consequential")

    def test_routine_approval_is_bound_to_its_actions_and_tab(self):
        _, env = self.routine_run(approve=True)
        other = [{"op": "click", "selector": "#delete"}]
        with env, patch.object(mcp_server, "browser_execute") as execute:
            call("browser.execute", session_id="tab-1", actions=other, approved_consequential=True)
            call("browser.execute", session_id="tab-2", actions=CLICK, approved_consequential=True)
            execute.assert_not_called()
            self.assertEqual(len(self.pending.list()), 2)

    def test_pending_record_reaches_the_window(self):
        """The window's /api/pending reads PendingStore(window_home()), the store MCP writes to."""
        from agent_os.executive.window.confirm import window_home

        batch_id = self.plan()
        call("executive.approve", batch_id=batch_id, choices={"ref-a": "confirm"})
        [record] = PendingStore(window_home()).list()
        self.assertEqual(record["action_id"], "executive.approve_batch")
        self.assertEqual(record["item"]["title"], f"Approve outreach batch {batch_id}")

    def test_no_mcp_tool_can_redeem_a_pending_record(self):
        """The window's Confirm click is the only way to redeem a parked record."""
        batch_id = self.plan()
        call("executive.approve", batch_id=batch_id, choices={"ref-a": "confirm"})
        [record] = self.pending.list()
        tools = {t["name"] for t in mcp_server._handle_mcp(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}, mcp_server.methods())["result"]["tools"]}
        self.assertFalse([n for n in tools if "confirm" in n.lower()], tools)
        for name in ("executive.approve", "executive.send", "browser.execute", "executive_window.run"):
            self.assertNotIn("confirm_token", mcp_server.TOOL_SCHEMAS.get(name, mcp_server.EXECUTIVE_TOOL_SCHEMAS.get(name, {}))
                             .get("inputSchema", {}).get("properties", {}))
        self.assertEqual(self.store.load(batch_id)["state"], ex.PENDING_APPROVAL)
        self.assertEqual([r["token"] for r in self.pending.list()], [record["token"]])

    def test_window_actions_are_consequential(self):
        actions = {a["id"]: a for a in self.reg.actions()}
        for action_id in ("executive.approve_batch", "executive.send_batch", "browser.execute_consequential"):
            self.assertTrue(actions[action_id]["consequential"], action_id)


if __name__ == "__main__":
    unittest.main()
