"""Host adapter for the standalone Shopping Agent (``unwit1/agent-os-shopping``).

Shopping owns its business logic: product matching, delivered-cost math, deal scoring, watches, approvals.
This module only carries owner requests to it and returns structured results. It does not import Shopping
internals; it talks to the versioned ``shopping.*`` operation contract through the Shopping CLI
(``agent-shopping --home H op NAME --args JSON``), one short-lived process per call. That keeps the two
repositories independently changeable and means a Shopping crash can never take the host down.

Safety boundary: only operations in ``ALLOWED_OPS`` can be called, and every call uses Shopping's model-safe
channel. Granting purchase authority, executing a purchase and promoting candidates are not callable from here.
Shopping also refuses them on that channel, so the boundary holds even if this allowlist is edited wrongly.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shlex
import shutil
import subprocess
import sys
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable

SUPPORTED_CONTRACT_MAJOR = 1
DEFAULT_TIMEOUT = 60.0
SLOW_TIMEOUT = 300.0     # searches and research hit remote sources

READ_OPS = frozenset({
    "shopping.contract", "shopping.doctor", "shopping.status", "shopping.sources.list",
    "shopping.want.list", "shopping.want.get", "shopping.want.origin", "shopping.wishlist.list",
    "shopping.research.list", "shopping.research.get", "shopping.price_history", "shopping.opportunities",
    "shopping.watch.list", "shopping.promotions.list", "shopping.sale_timing", "shopping.evaluate_deal",
    "shopping.cart.optimize", "shopping.order.list", "shopping.order.track", "shopping.return.evaluate",
})
WRITE_OPS = frozenset({
    "shopping.wishlist.add", "shopping.wishlist.remove", "shopping.want.update", "shopping.want.archive",
    "shopping.research.start", "shopping.research.adopt", "shopping.search", "shopping.watch.add",
    "shopping.watch.update", "shopping.watch.run", "shopping.cart.create", "shopping.checkout.handoff",
    "shopping.order.record", "shopping.order.update",
})
ALLOWED_OPS = READ_OPS | WRITE_OPS
SLOW_OPS = frozenset({"shopping.search", "shopping.watch.run", "shopping.research.start", "shopping.cart.create"})

INSTALL_HINT = ("Shopping Agent is not installed. Run `pip install -e <path to agent-os-shopping>` "
                "(or the Start-Shopping.ps1 launcher in that repository), then reload this page.")


def default_home() -> Path:
    return Path(os.environ.get("AGENT_SHOPPING_HOME") or Path.home() / ".agent-os-shopping")


def _error(code: str, message: str, *, retryable: bool = False, hint: str = "") -> dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message, "retryable": retryable, "hint": hint}}


def parse_command(text: str) -> list[str]:
    """``AGENT_SHOPPING_CMD``: a JSON array (preferred, what the Windows launcher writes) or a shell-style string."""
    if text.startswith("["):
        value = json.loads(text)
        if not isinstance(value, list) or not value or not all(isinstance(x, str) for x in value):
            raise ValueError("AGENT_SHOPPING_CMD must be a JSON array of strings")
        return value
    if os.name != "nt":
        return shlex.split(text)
    # Windows: non-POSIX shlex keeps quote characters inside tokens; strip one surrounding pair.
    return [t[1:-1] if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'" else t for t in shlex.split(text, posix=False)]


def locate_command() -> list[str] | None:
    """Find the Shopping CLI without any hard-coded user or checkout path."""
    configured = (os.environ.get("AGENT_SHOPPING_CMD") or "").strip()
    if configured:
        return parse_command(configured)
    exe = shutil.which("agent-shopping")
    if exe:
        return [exe]
    if importlib.util.find_spec("agent_shopping") is not None:
        return [sys.executable, "-m", "agent_shopping.cli"]
    from .paths import ROOT

    for base in (ROOT.parent, ROOT.parent.parent):
        script = base / "agent-os-shopping" / "shopping.py"
        if script.is_file():
            return [sys.executable, str(script)]
    return None


class ShoppingAdapter:
    def __init__(self, home: Path | str | None = None, command: list[str] | None = None, profile: str | None = None,
                 runner: Callable[..., Any] = subprocess.run, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.home = Path(home) if home else default_home()
        self._command = command
        self.profile = profile or os.environ.get("AGENT_SHOPPING_PROFILE") or None
        self._runner = runner
        self.timeout = timeout
        self._contract: dict[str, Any] | None = None
        self._seen: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._inflight: set[str] = set()
        self._lock = threading.Lock()

    # -- process boundary --------------------------------------------------------------
    def _run(self, op: str, args: dict[str, Any]) -> dict[str, Any]:
        command = self._command or locate_command()
        if not command:
            return _error("not_installed", "The Shopping Agent command was not found.", hint=INSTALL_HINT)
        argv = list(command) + ["--home", str(self.home)]
        if self.profile:
            argv += ["--profile", self.profile]
        argv += ["op", op, "--args", json.dumps(args, ensure_ascii=False)]
        limit = SLOW_TIMEOUT if op in SLOW_OPS else self.timeout
        kwargs: dict[str, Any] = {"capture_output": True, "text": True, "encoding": "utf-8", "timeout": limit,
                                  "env": {**os.environ, "PYTHONIOENCODING": "utf-8"}}
        if hasattr(subprocess, "CREATE_NO_WINDOW"):
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        try:
            done = self._runner(argv, **kwargs)
        except subprocess.TimeoutExpired:
            return _error("timeout", f"Shopping did not answer {op} within {int(limit)} seconds.", retryable=True,
                          hint="A source may be slow. Check Diagnostics.")
        except OSError as exc:
            return _error("not_installed", f"Could not start Shopping: {exc}", hint=INSTALL_HINT)
        text = (done.stdout or "").strip()
        try:
            payload = json.loads(text)
        except ValueError:
            tail = (done.stderr or text or "no output").strip()[-300:]
            return _error("process_failed", f"Shopping exited {done.returncode} without a JSON answer: {tail}",
                          retryable=True)
        if not isinstance(payload, dict) or "ok" not in payload:
            return _error("bad_output", "Shopping returned something that is not an operation result.")
        if payload["ok"]:
            return {"ok": True, "result": payload.get("result")}
        return _error("shopping_error", str(payload.get("message") or payload.get("error") or "unknown error"),
                      hint=str(payload.get("error") or ""))

    # -- contract negotiation ----------------------------------------------------------
    def contract(self) -> dict[str, Any]:
        if self._contract is not None:
            return {"ok": True, "result": self._contract}
        answer = self._run("shopping.contract", {})
        if not answer["ok"]:
            return answer
        info = answer["result"] or {}
        try:
            major = int(str(info.get("contract_version", "0")).split(".")[0])
        except ValueError:
            major = 0
        if major != SUPPORTED_CONTRACT_MAJOR:
            return _error("contract_mismatch",
                          f"Shopping speaks contract {info.get('contract_version')!r}; this host supports "
                          f"{SUPPORTED_CONTRACT_MAJOR}.x.", hint="Update agent-os-shopping or personal-agent-os.")
        self._contract = info
        return {"ok": True, "result": info}

    # -- public call ---------------------------------------------------------------------
    def call(self, op: str, args: dict[str, Any] | None = None, request_id: str | None = None) -> dict[str, Any]:
        """Run one allowed operation. Reads retry once on transient failure; writes never retry on their own."""
        if op not in ALLOWED_OPS:
            return _error("op_not_allowed", f"{op} is not available from the Command Center.",
                          hint="Purchase approval and execution are human-only and live in the Shopping CLI/dashboard.")
        args = dict(args or {})
        for forbidden in ("channel", "approver", "code"):
            args.pop(forbidden, None)
        if request_id and op in WRITE_OPS:
            with self._lock:
                if request_id in self._seen:
                    return {**self._seen[request_id], "duplicate": True}
                if request_id in self._inflight:
                    return _error("duplicate_in_progress", "This request is already being handled.", retryable=True)
                self._inflight.add(request_id)
            try:
                return self._call_once(op, args, request_id)
            finally:
                with self._lock:
                    self._inflight.discard(request_id)
        return self._call_once(op, args, None)

    def _call_once(self, op: str, args: dict[str, Any], request_id: str | None) -> dict[str, Any]:
        if op != "shopping.contract":
            negotiated = self.contract()
            if not negotiated["ok"]:
                return negotiated
            if op not in set(negotiated["result"].get("operations", [])):
                return _error("capability_missing", f"This Shopping version does not provide {op}.",
                              hint="Update agent-os-shopping.")
        answer = self._run(op, args)
        if not answer["ok"] and answer["error"]["retryable"] and op in READ_OPS:
            answer = self._run(op, args)
        if request_id and op in WRITE_OPS and answer["ok"]:
            with self._lock:
                self._seen[request_id] = answer
                while len(self._seen) > 256:
                    self._seen.popitem(last=False)
        return answer

    def health(self) -> dict[str, Any]:
        """Connected? Which version? Then Shopping's own doctor report."""
        contract = self.contract()
        if not contract["ok"]:
            return {"ok": False, "connected": False, "error": contract["error"]}
        report = self.call("shopping.doctor")
        if not report["ok"]:
            return {"ok": False, "connected": True, "contract": contract["result"], "error": report["error"]}
        return {"ok": True, "connected": True, "contract": contract["result"], "doctor": report["result"]}
