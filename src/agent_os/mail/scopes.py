"""Work/personal separation for mail.

Work mail (the EarthLink business accounts and the Outlook PST backups) and
personal mail (iCloud) are indexed into separate directories:
``.agent-local/mail/work/`` and ``.agent-local/mail/personal/``. An agent
reaches mail through a project, and a project sees only the scope set by its
``mail_scope`` in ``projects/registry.json``. A project without a
``mail_scope`` gets no mail at all.

This is a routing guardrail for cooperative agents, not an operating-system
permission: both directories remain readable by the local user.
"""

from __future__ import annotations

import shutil
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from . import accounts as accounts_lib
from . import config


class MailScopeError(PermissionError):
    pass


def project_scope(project: str) -> str:
    """The mail scope a project may read, or raise MailScopeError."""
    from ..registry import get_project

    if not project:
        raise MailScopeError("mail access needs a project; pass project=<registry id>")
    try:
        entry = get_project(project)
    except KeyError:
        raise MailScopeError(f"unknown project {project!r}") from None
    scope = entry.get("mail_scope")
    if scope not in config.SCOPES:
        raise MailScopeError(f"project {entry['id']} has no mail access (set mail_scope to work or personal in projects/registry.json)")
    return scope


def accounts_in(scope: str) -> list[accounts_lib.Account]:
    return [item for item in accounts_lib.load_accounts() if item.mail_scope == config.check_scope(scope)]


def split_combined_index(source: Path | None = None) -> dict[str, Any]:
    """One-time move from the single ``index.sqlite3`` to per-scope indexes.

    Copies the combined index into each scope, deletes the other scope's
    observations, messages, attachments, search rows and mailbox state from
    each copy, moves per-account ledgers, verifies, then deletes the combined
    file (it mixed work and personal mail). Archives always count as work.
    """
    source = Path(source or config.DB)
    if not source.exists():
        return {"split": False, "reason": "no combined index"}
    by_scope = {scope: {item.id for item in accounts_in(scope)} for scope in config.SCOPES}
    with closing(sqlite3.connect(source)) as conn:
        present = {row[0] for row in conn.execute("SELECT DISTINCT account_id FROM mail_sources WHERE account_id IS NOT NULL")}
        before = conn.execute("SELECT COUNT(*) FROM mail_sources").fetchone()[0]
    unknown = present - set().union(*by_scope.values())
    if unknown:
        raise ValueError(f"index has mail for accounts that are not configured: {sorted(unknown)}; add them or remove the index first")
    result: dict[str, Any] = {"split": True, "observations_before": before}
    for scope in config.SCOPES:
        target = config.db_for(scope)
        if target.exists():
            raise ValueError(f"{target} already exists; the split has already run")
        target.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(source)) as src, closing(sqlite3.connect(target)) as dst:
            src.backup(dst)
        keep = sorted(by_scope[scope])
        marks = ",".join("?" * len(keep)) or "NULL"
        with closing(sqlite3.connect(target)) as conn:
            archive_clause = "" if scope == "work" else " OR source_kind != 'live_imap'"
            conn.execute(f"DELETE FROM mail_sources WHERE (source_kind = 'live_imap' AND (account_id IS NULL OR account_id NOT IN ({marks}))){archive_clause}", keep)
            conn.execute(f"DELETE FROM mail_mailboxes WHERE account_id NOT IN ({marks})", keep)
            conn.execute("DELETE FROM mail_attachments WHERE message_id NOT IN (SELECT message_id FROM mail_sources)")
            try:
                conn.execute("DELETE FROM mail_fts WHERE message_id NOT IN (SELECT message_id FROM mail_sources)")
            except sqlite3.OperationalError:
                pass
            conn.execute("DELETE FROM mail_messages WHERE id NOT IN (SELECT message_id FROM mail_sources)")
            conn.commit()
            result[scope] = {
                "observations": conn.execute("SELECT COUNT(*) FROM mail_sources").fetchone()[0],
                "messages": conn.execute("SELECT COUNT(*) FROM mail_messages").fetchone()[0],
            }
            conn.execute("VACUUM")
        for account_id in keep:
            old = config.LEDGER_DIR / account_id
            if old.exists():
                config.ledger_dir_for(scope).mkdir(parents=True, exist_ok=True)
                shutil.move(str(old), str(config.ledger_dir_for(scope) / account_id))
    archives = config.LEDGER_DIR / "archives"
    if archives.exists():
        shutil.move(str(archives), str(config.ledger_dir_for("work") / "archives"))
    if result["work"]["observations"] + result["personal"]["observations"] != before:
        raise RuntimeError("split verification failed; the combined index was kept")
    source.unlink()
    for suffix in ("-wal", "-shm"):
        Path(str(source) + suffix).unlink(missing_ok=True)
    return result
