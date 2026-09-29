"""Orchestrator OS continuation: checkpoint + exact next prompt, no model call.

``status.json`` (projects/personal-agent-os/orchestrator-os/) is the
hand/agent-maintained project manifest: phase, completed work, active
objective, next action, blockers, decisions. ``build`` projects it together
with Git state and the latest evidence records into an ``ORCH-NNNN``
checkpoint (schemas/orchestrator-checkpoint-v1.schema.json) and renders the
next prompt from a fixed template. The prompt references the canonical
entrypoint and the checkpoint; it never restates the architecture.

    agent-os orchestrate checkpoint            # preview
    agent-os orchestrate checkpoint --write    # persist ORCH-NNNN + next-prompt.md
    agent-os orchestrate next-prompt           # print the current next prompt
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from ..paths import ROOT
from ..timestamps import utc_now_iso

OS_DIR = ROOT / "projects" / "personal-agent-os" / "orchestrator-os"
STATUS_PATH = OS_DIR / "status.json"
CHECKPOINTS = OS_DIR / "checkpoints"
RECORDS = OS_DIR / "records"
NEXT_PROMPT = OS_DIR / "next-prompt.md"
ENTRYPOINT = "docs/orchestrator-os/ENTRYPOINT.md"
_ID = re.compile(r"^ORCH-(\d{4,})\.json$")

TEMPLATE = """Use the Personal Agent OS repository's canonical Orchestrator development workflow ({entrypoint}) and resume from checkpoint {checkpoint_id} ({checkpoint_path}).

Current objective: {objective}

Next action: {next_action}
{prior_art}
Retrieve only the context referenced by the checkpoint (`agent-os orchestrate checkpoint --show`); load more lazily if needed. Recommended worker class: {worker_class}. Delegate cheap read-only work with `agent-os orchestrate delegate` and use the cheapest reliable route under policy/orchestrator-os.policy.json. Baseline before changing behavior, keep protected control-plane paths untouched unless I grant them, and stop at: {stop}.

Finish by updating projects/personal-agent-os/orchestrator-os/status.json and running `agent-os orchestrate checkpoint --write`, then give me the new next prompt.
"""


def _git(*args: str) -> str | None:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=20, check=True).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def load_status(path: Path | None = None) -> dict[str, Any]:
    return json.loads(Path(path or STATUS_PATH).read_text(encoding="utf-8"))


def checkpoint_paths(directory: Path | None = None) -> list[Path]:
    root = Path(directory or CHECKPOINTS)
    return sorted((path for path in root.glob("ORCH-*.json") if _ID.match(path.name)), key=lambda path: int(_ID.match(path.name).group(1)))


def latest(directory: Path | None = None) -> dict[str, Any] | None:
    paths = checkpoint_paths(directory)
    return json.loads(paths[-1].read_text(encoding="utf-8")) if paths else None


def next_id(directory: Path | None = None) -> str:
    paths = checkpoint_paths(directory)
    number = int(_ID.match(paths[-1].name).group(1)) + 1 if paths else 1
    return f"ORCH-{number:04d}"


def recent_evidence(limit: int = 8, records: Path | None = None) -> list[dict[str, str]]:
    root = Path(records or RECORDS)
    items = []
    for path in root.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and data.get("id") and data.get("type"):
            items.append({"id": data["id"], "type": data["type"], "title": str(data.get("title", ""))[:120], "path": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path), "updated_at": str(data.get("updated_at") or data.get("created_at") or "")})
    items.sort(key=lambda item: item["updated_at"], reverse=True)
    return items[:limit]


def render_prompt(checkpoint: dict[str, Any]) -> str:
    action = checkpoint["next_action"]
    return TEMPLATE.format(
        entrypoint=ENTRYPOINT,
        checkpoint_id=checkpoint["id"],
        checkpoint_path=f"projects/personal-agent-os/orchestrator-os/checkpoints/{checkpoint['id']}.json",
        objective=checkpoint["active_objective"],
        next_action=action["summary"],
        prior_art=(f"\nBefore implementing, consult the prior-art registry (`agent-os orchestrate prior-art lookup \"{action['prior_art']}\"`) and refresh task-specific candidates if the matching entries are stale.\n" if action.get("prior_art") else ""),
        worker_class=f"{action.get('worker_class', 'balanced')} / effort {action.get('effort', 'medium')}",
        stop="; ".join(checkpoint.get("stopping_conditions") or ["objective validator passes"]),
    )


def build(status: dict[str, Any] | None = None, *, checkpoint_id: str | None = None, directory: Path | None = None) -> dict[str, Any]:
    status = status if status is not None else load_status()
    previous = latest(directory)
    checkpoint = {
        "schema": "personal-agent/orchestrator-checkpoint/v1",
        "id": checkpoint_id or next_id(directory),
        "previous": previous["id"] if previous else None,
        "created_at": utc_now_iso(),
        "git": {"branch": _git("rev-parse", "--abbrev-ref", "HEAD"), "commit": _git("rev-parse", "--short", "HEAD"), "dirty": bool(_git("status", "--porcelain"))},
        "phase": status["phase"],
        "completed": status.get("completed", [])[-12:],
        "active_objective": status["active_objective"],
        "latest_evidence": recent_evidence(),
        "open_blockers": status.get("blockers", []),
        "active_experiments": status.get("active_experiments", []),
        "recent_decisions": status.get("recent_decisions", [])[-6:],
        "next_action": status["next_action"],
        "context_refs": status["next_action"].get("context_refs", []),
        "stopping_conditions": status["next_action"].get("stop_conditions", []),
        "approval_conditions": status.get("approval_conditions", []),
    }
    checkpoint["next_prompt"] = render_prompt(checkpoint)
    return checkpoint


def write(checkpoint: dict[str, Any], directory: Path | None = None, prompt_path: Path | None = None) -> dict[str, str]:
    root = Path(directory or CHECKPOINTS)
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{checkpoint['id']}.json"
    if path.exists():
        raise FileExistsError(f"{path.name} already exists; checkpoints are immutable")
    path.write_text(json.dumps(checkpoint, indent=2) + "\n", encoding="utf-8", newline="\n")
    target = Path(prompt_path or NEXT_PROMPT)
    target.write_text(f"<!-- generated by `agent-os orchestrate checkpoint --write` from {checkpoint['id']}; do not edit -->\n\n" + checkpoint["next_prompt"], encoding="utf-8", newline="\n")
    return {"checkpoint": str(path), "next_prompt": str(target)}
