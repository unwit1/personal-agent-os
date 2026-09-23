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

# Work and personal mail live in separate directories, each with its own
# index and ledgers, so a project can be given one without the other.
SCOPES = ("work", "personal")


def check_scope(scope: str) -> str:
    if scope not in SCOPES:
        raise ValueError(f"mail scope must be one of: {', '.join(SCOPES)}")
    return scope


def scope_dir(scope: str) -> Path:
    return LOCAL_DIR / check_scope(scope)


def db_for(scope: str) -> Path:
    return scope_dir(scope) / "index.sqlite3"


def ledger_dir_for(scope: str) -> Path:
    return scope_dir(scope) / "ledgers"
