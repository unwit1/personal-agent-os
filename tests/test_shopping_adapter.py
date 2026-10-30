import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import http.client
import json
import os
import subprocess
import tempfile
import threading
import unittest
from types import SimpleNamespace

from agent_os.executive.window.registry import Registry
from agent_os.executive.window.server import build_server
from agent_os.shopping_adapter import ALLOWED_OPS, ShoppingAdapter

CONTRACT = {"contract_version": "1.0", "operations": sorted(ALLOWED_OPS)}


class FakeRunner:
    """Stands in for the Shopping CLI process; records argv, answers from a script."""

    def __init__(self, answers=None):
        self.calls = []
        self.answers = answers or {}

    def __call__(self, argv, **kwargs):
        op = argv[argv.index("op") + 1]
        args = json.loads(argv[argv.index("--args") + 1])
        self.calls.append((op, args, argv))
        answer = self.answers.get(op)
        if callable(answer):
            answer = answer(len(self.calls))
        if answer is None:
            answer = {"ok": True, "result": CONTRACT} if op == "shopping.contract" else {"ok": True, "result": {"echo": args}}
        if isinstance(answer, Exception):
            raise answer
        return SimpleNamespace(stdout=answer if isinstance(answer, str) else json.dumps(answer), stderr="", returncode=0)


def adapter(runner, **kw):
    return ShoppingAdapter(home="/tmp/shop-home", command=["shopping"], runner=runner, **kw)


class AdapterTests(unittest.TestCase):
    def test_allowlist_blocks_human_only_and_purchase_operations(self):
        runner = FakeRunner()
        a = adapter(runner)
        for op in ("shopping.approval.grant", "shopping.approval.create", "shopping.purchase.execute",
                   "shopping.purchase.prepare", "shopping.candidate.promote", "shopping.listing.ingest", "rm -rf"):
            out = a.call(op, {})
            self.assertFalse(out["ok"], op)
            self.assertEqual(out["error"]["code"], "op_not_allowed", op)
        self.assertEqual(runner.calls, [])                       # never even reached the process

    def test_forged_authority_arguments_are_stripped(self):
        runner = FakeRunner()
        adapter(runner).call("shopping.want.list", {"status": "active", "channel": "human", "approver": "me", "code": "123"})
        sent = [c for c in runner.calls if c[0] == "shopping.want.list"][0][1]
        self.assertEqual(sent, {"status": "active"})

    def test_contract_major_mismatch_is_reported(self):
        a = adapter(FakeRunner({"shopping.contract": {"ok": True, "result": {"contract_version": "2.0", "operations": []}}}))
        out = a.call("shopping.want.list")
        self.assertEqual(out["error"]["code"], "contract_mismatch")

    def test_missing_capability_is_reported(self):
        a = adapter(FakeRunner({"shopping.contract": {"ok": True, "result": {"contract_version": "1.3", "operations": ["shopping.want.list"]}}}))
        self.assertEqual(a.call("shopping.doctor")["error"]["code"], "capability_missing")

    def test_read_retries_once_on_transient_failure_but_write_does_not(self):
        flaky = lambda n: "not json" if n <= 2 else {"ok": True, "result": []}      # call 1 = contract, 2 = first attempt
        runner = FakeRunner({"shopping.want.list": flaky})
        self.assertTrue(adapter(runner).call("shopping.want.list")["ok"])
        self.assertEqual([c[0] for c in runner.calls].count("shopping.want.list"), 2)
        runner = FakeRunner({"shopping.wishlist.add": "garbage"})
        out = adapter(runner).call("shopping.wishlist.add", {"want": {"description": "x"}})
        self.assertEqual(out["error"]["code"], "process_failed")
        self.assertEqual([c[0] for c in runner.calls].count("shopping.wishlist.add"), 1)

    def test_timeout_and_missing_install_are_structured(self):
        out = adapter(FakeRunner({"shopping.contract": subprocess.TimeoutExpired("x", 1)})).call("shopping.want.list")
        self.assertEqual(out["error"]["code"], "timeout")
        self.assertTrue(out["error"]["retryable"])
        out = adapter(FakeRunner({"shopping.contract": FileNotFoundError("nope")})).call("shopping.want.list")
        self.assertEqual(out["error"]["code"], "not_installed")
        self.assertIn("pip install", out["error"]["hint"])

    def test_shopping_errors_keep_their_message(self):
        a = adapter(FakeRunner({"shopping.want.get": {"ok": False, "error": "WantError", "message": "unknown want x"}}))
        out = a.call("shopping.want.get", {"want_id": "x"})
        self.assertEqual(out["error"]["code"], "shopping_error")
        self.assertEqual(out["error"]["message"], "unknown want x")

    def test_duplicate_write_request_is_answered_once(self):
        runner = FakeRunner()
        a = adapter(runner)
        first = a.call("shopping.wishlist.add", {"want": {"description": "x"}}, request_id="r1")
        again = a.call("shopping.wishlist.add", {"want": {"description": "x"}}, request_id="r1")
        self.assertTrue(first["ok"])
        self.assertTrue(again.get("duplicate"))
        self.assertEqual([c[0] for c in runner.calls].count("shopping.wishlist.add"), 1)

    def test_home_and_profile_are_passed_not_hardcoded(self):
        runner = FakeRunner()
        adapter(runner, profile="alex").call("shopping.want.list")
        argv = runner.calls[-1][2]
        self.assertIn("/tmp/shop-home", argv)
        self.assertEqual(argv[argv.index("--profile") + 1], "alex")


class WindowRouteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.runner = FakeRunner({"shopping.doctor": {"ok": True, "result": {"ok": True, "problems": [], "actions": []}}})
        self.server, self.token = build_server("127.0.0.1", 0, registry=Registry(), bridge=SimpleNamespace(send=lambda *a: {}),
                                               home=Path(self.tmp.name), shopping=adapter(self.runner))
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def post(self, body, token=True):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        headers = {"Host": f"127.0.0.1:{self.port}", "Content-Type": "application/json"}
        if token:
            headers["X-Agent-OS-Token"] = self.token
        conn.request("POST", "/api/shopping", body=json.dumps(body), headers=headers)
        r = conn.getresponse()
        data = json.loads(r.read())
        conn.close()
        return r.status, data

    def test_requires_token(self):
        status, _ = self.post({"op": "shopping.want.list"}, token=False)
        self.assertEqual(status, 403)
        self.assertEqual(self.runner.calls, [])

    def test_get_is_not_a_route(self):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request("GET", "/api/shopping", headers={"Host": f"127.0.0.1:{self.port}"})
        self.assertEqual(conn.getresponse().status, 404)

    def test_forwarded_and_blocked_ops(self):
        status, data = self.post({"op": "shopping.want.list", "args": {}})
        self.assertEqual((status, data["ok"]), (200, True))
        status, data = self.post({"op": "shopping.approval.grant", "args": {"request_id": "r", "code": "1"}})
        self.assertEqual(data["error"]["code"], "op_not_allowed")
        status, data = self.post({"op": "health"})
        self.assertTrue(data["connected"])

    def test_research_start_is_always_detached(self):
        self.post({"op": "shopping.research.start", "args": {"text": "a lamp"}})
        sent = [c for c in self.runner.calls if c[0] == "shopping.research.start"][0][1]
        self.assertTrue(sent["detach"])

    def test_page_and_assets_are_served_with_shopping_tab(self):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        for path, needle in (("/", "tab-shopping"), ("/shopping.js", "ShoppingTab"), ("/shopping.css", ".sp-")):
            conn.request("GET", path, headers={"Host": f"127.0.0.1:{self.port}"})
            r = conn.getresponse()
            body = r.read().decode("utf-8")
            self.assertEqual(r.status, 200, path)
            self.assertIn(needle, body, path)


@unittest.skipUnless(__import__("importlib").util.find_spec("agent_shopping"), "agent-os-shopping is not installed here")
class RealShoppingProcessTests(unittest.TestCase):
    """Adapter against the real Shopping CLI in a temporary home (fixture/demo stores only)."""

    def test_round_trip_and_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = ShoppingAdapter(home=tmp, command=[sys.executable, "-m", "agent_shopping.cli"])
            health = a.health()
            self.assertTrue(health["connected"], health)
            self.assertEqual(health["doctor"]["data_mode"], "empty")
            added = a.call("shopping.wishlist.add", {"want": {"description": "Sonix WH-100", "target_price": "90"}})
            self.assertTrue(added["ok"], added)
            again = ShoppingAdapter(home=tmp, command=[sys.executable, "-m", "agent_shopping.cli"])    # "restart"
            listed = again.call("shopping.wishlist.list")
            self.assertEqual([w["description"] for w in listed["result"]], ["Sonix WH-100"])
            denied = again.call("shopping.approval.grant", {})
            self.assertEqual(denied["error"]["code"], "op_not_allowed")


if __name__ == "__main__":
    unittest.main()
