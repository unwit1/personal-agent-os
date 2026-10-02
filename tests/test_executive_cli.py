from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os import cli
from agent_os.executive import applicants as ex


class MemStore:
    def __init__(self, *batches):
        self.batches = {b["batch_id"]: b for b in batches}

    def save(self, batch):
        self.batches[batch["batch_id"]] = json.loads(json.dumps(batch))

    def load(self, batch_id):
        return json.loads(json.dumps(self.batches[batch_id]))


GATEWAY = object()


def run(*argv, store=None):
    out = io.StringIO()
    with patch.object(cli, "_executive_gateway", return_value=GATEWAY), patch.object(
        cli, "_executive_store", return_value=store or MemStore()
    ), contextlib.redirect_stdout(out):
        code = cli.main(["executive", *argv])
    return code, json.loads(out.getvalue())


class ExecutiveCliRouting(unittest.TestCase):
    def test_needs_action(self):
        with patch.object(ex, "needs_action", return_value={"groups": []}) as fn:
            code, out = run("needs-action", "--limit", "5")
        self.assertEqual((code, out), (0, {"groups": []}))
        fn.assert_called_once_with(limit=5)

    def test_suggestions(self):
        with patch.object(ex, "suggestions", return_value={"ok": 1}) as fn:
            code, _ = run("suggestions", "Technician")
        self.assertEqual(code, 0)
        fn.assert_called_once_with("Technician", gateway=GATEWAY)

    def test_plan_accepts_inline_and_file_refs(self):
        store = MemStore()
        with patch.object(ex, "plan_outreach", return_value={"batch_id": "b"}) as fn:
            run("plan", "--opening", "Tech", "--applicant-refs", '["a","b"]',
                "--interview-type", "phone", "--location", "HQ", "--duration-minutes", "45", store=store)
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp, "refs.json")
                path.write_text('["c"]', encoding="utf-8")
                run("plan", "--opening", "Tech", "--applicant-refs", str(path),
                    "--interview-type", "phone", "--location", "HQ", store=store)
        first, second = fn.call_args_list
        self.assertEqual(first.args, (["a", "b"], "Tech", "phone", "HQ", 45))
        self.assertEqual(second.args, (["c"], "Tech", "phone", "HQ", 30))
        self.assertIs(first.kwargs["store"], store)
        self.assertIs(first.kwargs["gateway"], GATEWAY)

    def test_plan_rejects_non_list_refs(self):
        code, out = run("plan", "--opening", "T", "--applicant-refs", '{"a":1}',
                        "--interview-type", "x", "--location", "y")
        self.assertEqual(code, 2)
        self.assertIn("error", out)

    def test_inspect_and_unknown_batch(self):
        store = MemStore({"batch_id": "b1", "state": "PENDING_APPROVAL", "items": []})
        self.assertEqual(run("batch", "b1", store=store)[1]["state"], "PENDING_APPROVAL")
        self.assertEqual(run("batch", "nope", store=store)[0], 2)

    def test_approve_passes_choices(self):
        choices = {"a": "confirm", "b": "drop", "c": ["2026-10-05T10:00"]}
        with patch.object(ex, "approve_batch", return_value={"state": "APPROVED"}) as fn:
            code, _ = run("approve", "b1", "--choices", json.dumps(choices))
        self.assertEqual(code, 0)
        self.assertEqual(fn.call_args.args, ("b1", choices))

    def test_send_defaults_to_dry_run_and_shows_approval_state(self):
        batch = {
            "batch_id": "b1",
            "state": "APPROVED",
            "items": [{"applicant_ref": "a", "state": "APPROVED", "decision": "confirmed"}],
        }
        with patch.object(ex, "send_batch", return_value={"sent": 0}) as fn:
            code, out = run("send", "b1", store=MemStore(batch))
        self.assertEqual(code, 0)
        self.assertIs(fn.call_args.kwargs["confirm"], False)
        self.assertIsNone(fn.call_args.kwargs["gateway"])
        self.assertTrue(out["dry_run"])
        self.assertEqual(out["approval"]["state"], "APPROVED")
        self.assertEqual(out["approval"]["items"][0]["decision"], "confirmed")

    def test_send_confirm_flag(self):
        batch = {"batch_id": "b1", "state": "APPROVED", "items": []}
        with patch.object(ex, "send_batch", return_value={}) as fn:
            code, out = run("send", "b1", "--confirm", store=MemStore(batch))
        self.assertIs(fn.call_args.kwargs["confirm"], True)
        self.assertIs(fn.call_args.kwargs["gateway"], GATEWAY)
        self.assertFalse(out["dry_run"])

    def test_send_unapproved_batch_errors(self):
        batch = {"batch_id": "b1", "state": "PENDING_APPROVAL", "items": []}
        code, out = run("send", "b1", "--confirm", store=MemStore(batch))
        self.assertEqual(code, 2)
        self.assertIn("approve", out["error"])


if __name__ == "__main__":
    unittest.main()
