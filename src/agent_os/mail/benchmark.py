"""`agent-os mail benchmark`: timing for the real sync engine, ledger and
index against an in-memory synthetic IMAP server (no network, no real mail).

Measures first import, a no-change resync, a small delta, and search latency
(full-text and filtered, across two accounts). Informative only; results go
to ``.agent-local/mail/benchmarks/``.
"""

from __future__ import annotations

import json
import re
import shutil
import tempfile
import time
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any
from unittest import mock

from . import accounts as accounts_lib
from . import config
from .engine import sync_account
from .store import Store

WORDS = "benefits payroll enrollment schedule invoice meeting garden report travel policy onboarding review contract budget".split()


def _message(index: int, account: str) -> bytes:
    msg = EmailMessage()
    msg["From"] = f"Sender {index % 37} <s{index % 37}@example.test>"
    msg["To"] = f"{account}@example.test"
    msg["Subject"] = f"{WORDS[index % len(WORDS)].title()} update {index}"
    msg["Date"] = f"{(index % 28) + 1:02d} Aug 2026 10:{index % 60:02d}:00 +0000"
    msg["Message-ID"] = f"<bench-{account}-{index}@example.test>"
    msg.set_content(" ".join(WORDS[(index + offset) % len(WORDS)] for offset in range(60)) + f" token{index}")
    return bytes(msg)


class _Server:
    def __init__(self, messages: dict[int, bytes]) -> None:
        self.messages = messages

    def factory(self, host, port, ssl_context=None, timeout=None):
        return _Client(self)


class _Client:
    def __init__(self, server: _Server) -> None:
        self.server = server

    def login(self, user, password):
        return "OK", []

    def capability(self):
        return "OK", [b"IMAP4rev1"]

    def select(self, mailbox, readonly=False):
        return "OK", [str(len(self.server.messages)).encode()]

    def response(self, name):
        return name, [b"1"] if name == "UIDVALIDITY" else [None]

    def uid(self, command, *args):
        if command == "search":
            return "OK", [" ".join(map(str, sorted(self.server.messages))).encode()]
        wanted = []
        for part in args[0].split(","):
            if ":" in part:
                start, end = map(int, part.split(":"))
                wanted += [uid for uid in range(start, end + 1) if uid in self.server.messages]
            elif int(part) in self.server.messages:
                wanted.append(int(part))
        data = []
        for uid in wanted:
            raw = self.server.messages[uid]
            meta = f'{uid} (UID {uid} RFC822.SIZE {len(raw)} INTERNALDATE "01-Aug-2026 10:00:00 +0000" FLAGS ()'
            data += [(f"{meta} BODY[] {{{len(raw)}}}".encode(), raw), b")"] if "PEEK" in args[1] else [(meta + ")").encode()]
        return "OK", data

    def logout(self):
        return "BYE", []


def run(messages: int = 1000, out_dir: Path | None = None) -> dict[str, Any]:
    root = Path(tempfile.mkdtemp(prefix="agent-os-mail-bench-"))
    results: dict[str, Any] = {"messages_per_account": messages, "accounts": 2}
    try:
        local = root / "mail"
        patches = [mock.patch.object(config, name, value) for name, value in {
            "LOCAL_DIR": local, "ACCOUNTS_FILE": local / "accounts.json", "LEGACY_CONFIG": local / "icloud.json",
            "DB": local / "index.sqlite3", "LEDGER_DIR": local / "ledgers", "LOG_FILE": local / "log.jsonl"}.items()]
        for patch in patches:
            patch.start()
        try:
            with mock.patch.dict("os.environ", {accounts_lib.env_name("bench-work"): "x", accounts_lib.env_name("bench-home"): "x"}):
                work = accounts_lib.add_account("earthlink", "bench-work", "w@example.test")
                home = accounts_lib.add_account("icloud", "bench-home", "h@example.test")
                servers = {account.id: _Server({uid: _message(uid, account.id) for uid in range(1, messages + 1)}) for account in (work, home)}

                def sync_all(**kwargs: Any) -> float:
                    started = time.perf_counter()
                    for account in (work, home):
                        sync_account(account, store_path=local / "index.sqlite3", ledger_dir=local / "ledgers", connect_factory=servers[account.id].factory, limit=messages, batch=100, **kwargs)
                    return round(time.perf_counter() - started, 3)

                results["first_import_seconds"] = sync_all()
                results["no_change_resync_seconds"] = sync_all()
                for account in (work, home):
                    for uid in range(messages + 1, messages + 11):
                        servers[account.id].messages[uid] = _message(uid, account.id)
                results["delta_10_per_account_seconds"] = sync_all()
                with Store(local / "index.sqlite3") as store:
                    results["logical_messages"] = store.counts()["logical_messages"]
                    results["fts"] = store.fts
                    for label, kwargs in (
                        ("search_fulltext_ms", {"query": "payroll budget"}),
                        ("search_rare_token_ms", {"query": f"token{messages // 2}"}),
                        ("search_filtered_ms", {"query": "enrollment", "accounts": ["bench-work"], "after": "2026-08-10", "sender": "s3@"}),
                        ("search_recent_no_query_ms", {"query": ""}),
                    ):
                        started = time.perf_counter()
                        for _ in range(20):
                            store.search(**kwargs)
                        results[label] = round((time.perf_counter() - started) * 1000 / 20, 2)
                results["ledger_bytes"] = sum(path.stat().st_size for path in (local / "ledgers").rglob("*.json"))
                results["index_bytes"] = (local / "index.sqlite3").stat().st_size
        finally:
            for patch in patches:
                patch.stop()
    finally:
        shutil.rmtree(root, ignore_errors=True)
    results["at"] = datetime.now(timezone.utc).isoformat()
    target = Path(out_dir or config.LOCAL_DIR / "benchmarks")
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"mail-benchmark-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    results["file"] = str(path)
    return results
