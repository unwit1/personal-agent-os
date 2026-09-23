"""Local paths for the mail subsystem (all under the gitignored .agent-local)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LOCAL_DIR = ROOT / ".agent-local" / "mail"
LEGACY_CONFIG = LOCAL_DIR / "icloud.json"
ACCOUNTS_FILE = LOCAL_DIR / "accounts.json"
DB = LOCAL_DIR / "index.sqlite3"
LEDGER_DIR = LOCAL_DIR / "ledgers"
LOG_FILE = LOCAL_DIR / "sync-log.jsonl"
