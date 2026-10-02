"""Mail cleanup: the 'Organize inbox' item, plan cache and per-category apply actions."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable

from .confirm import window_home

PLAN_FILE = "mail-organize-plan.json"
TABS = ("work", "personal")

# Injection hooks (tests): BUILD_PLAN() -> plan dict; MOVERS(account) -> Mover; ACCOUNTS -> accounts list/dict.
BUILD_PLAN: Callable[..., dict[str, Any]] | None = None
MOVERS: Callable[[Any], Any] | None = None
ACCOUNTS: Any = None
JOURNAL_PATH: Any = None  # tests: keep the journal out of the real mail home


def _plan_path():
    return window_home() / PLAN_FILE


def _load_plan() -> dict[str, Any] | None:
    try:
        data = json.loads(_plan_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def mail_cleanup_items() -> list[dict[str, Any]]:
    """One cleanup item per tab. Reads the cached plan only; never builds one."""
    cached = _load_plan()
    items = []
    for tab in TABS:
        plan = None
        spam_filtered: Any = None
        generated_at = None
        if cached:
            accounts = {k: v for k, v in (cached.get("accounts") or {}).items() if v.get("scope") == tab}
            plan = accounts
            generated_at = cached.get("generated_at")
            sf = cached.get("spam_filtered") or {}
            by_account = {k: v for k, v in (sf.get("by_account") or {}).items() if k in accounts}
            spam_filtered = {**{k: v for k, v in sf.items() if k != "by_account"}, "by_account": by_account}
        items.append({
            "id": f"mail:cleanup:{tab}",
            "tab": tab,
            "kind": "mail_cleanup",
            "title": "Organize inbox",
            "why": "Review the inbox organization plan" if cached else "No plan yet: run Organize inbox",
            "source": "mail",
            "context": {"plan": plan, "spam_filtered": spam_filtered, "generated_at": generated_at},
        })
    return items


def _build_plan() -> dict[str, Any]:
    if BUILD_PLAN is not None:
        return BUILD_PLAN()
    from agent_os.mail import organize
    return organize.build_plan()


def organize_inbox(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    plan = _build_plan()
    plan.setdefault("generated_at", datetime.now(timezone.utc).isoformat())
    path = _plan_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, default=str), encoding="utf-8")
    counts = {acct: {c: b.get("count", 0) for c, b in (e.get("categories") or {}).items()}
              for acct, e in (plan.get("accounts") or {}).items()}
    return {"plan_written": str(path), "generated_at": plan.get("generated_at"), "counts": counts,
            "spam_filtered": plan.get("spam_filtered")}


def organize_apply(item: dict[str, Any], params: dict[str, Any], *, confirm: bool) -> dict[str, Any]:
    account, category = params.get("account"), params.get("category")
    if not account or not category:
        raise ValueError("account and category are required")
    plan = _load_plan()
    if plan is None:
        raise ValueError("no organization plan cached: run Organize inbox first")
    from agent_os.mail import organize_apply as apply_mod
    result = apply_mod.apply_plan(plan, category, accounts=ACCOUNTS, only_accounts=[account],
                                  dry_run=not confirm, connect=MOVERS, journal_path=JOURNAL_PATH)
    if not confirm:
        return result
    journal_id = result.get("journal_id")
    return {**result, "move_id": journal_id,
            "undo_command": f"agent-os mail organize-undo --journal {journal_id}" if journal_id else None}


def register(registry: Any) -> None:
    registry.register_action(
        "mail.organize_inbox", "Organize inbox", ["mail_cleanup"], organize_inbox, consequential=False,
        description="Build the inbox organization plan (no mail is moved)")
    registry.register_action(
        "mail.organize_apply", "Apply category", ["mail_cleanup"], organize_apply, consequential=True,
        description="Move one category of an account's inbox mail into its target folder (reversible, journaled)",
        params_schema={"type": "object",
                       "properties": {"account": {"type": "string", "description": "Account id"},
                                      "category": {"type": "string", "description": "Plan category"}},
                       "required": ["account", "category"]})
