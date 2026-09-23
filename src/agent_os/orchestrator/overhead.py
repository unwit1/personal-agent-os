"""Measure the fixed per-call context cost of each coding-agent CLI.

``agent-os orchestrate overhead`` sends the same trivial prompt ("reply OK,
use no tools") through the real adapter once per option variant, in two
different throwaway worktrees of the target repository. With a one-word
answer and no tool use, the provider-reported input tokens are almost
entirely what the CLI sends on its own with every call: system prompt, tool
definitions, skill/plugin listings, instruction files. The second worktree
shows whether that prefix is served from the prompt cache or written again.

Every number is the provider's exact report; nothing is estimated. Each probe
is a real (small) model call, so this command spends usage.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .adapters import AgentLaunchRequest, get_adapter
from .router import ProviderRegistry
from .store import orchestrator_home
from .worktrees import git, repository_root

PROBE_PROMPT = "Reply with exactly the word OK and nothing else. Do not read files and do not use any tools.\n"

VARIANTS: dict[str, list[tuple[str, dict[str, Any]]]] = {
    "claude_code": [
        ("current", {"lean_tools": False, "disable_skills": False, "shared_prompt_cache": False, "setting_sources": None}),
        ("lean_tools", {"lean_tools": True, "disable_skills": False, "shared_prompt_cache": False, "setting_sources": None}),
        ("no_skills", {"lean_tools": False, "disable_skills": True, "shared_prompt_cache": False, "setting_sources": None}),
        ("shared_cache", {"lean_tools": False, "disable_skills": False, "shared_prompt_cache": True, "setting_sources": None}),
        ("project_settings_only", {"lean_tools": False, "disable_skills": False, "shared_prompt_cache": False, "setting_sources": "project,local"}),
        ("all_lean", {"lean_tools": True, "disable_skills": True, "shared_prompt_cache": True, "setting_sources": "project,local"}),
    ],
    "codex_cli": [
        ("current", {"use_user_config": True, "disable_features": []}),
        ("ignore_user_config", {"use_user_config": False, "disable_features": []}),
    ],
}


def _worktrees(repo: Path, root: Path, count: int) -> list[Path]:
    paths = []
    for index in range(count):
        path = root / f"wt{index}"
        git(["worktree", "add", "--detach", str(path), "HEAD"], repo)
        paths.append(path)
    return paths


def _probe(provider: dict[str, Any], options: dict[str, Any], cwd: Path, out: Path, capability_class: str, timeout: float) -> dict[str, Any]:
    entry = {**provider, "options": {**(provider.get("options") or {}), **options}}
    adapter = get_adapter(entry)
    out.mkdir(parents=True, exist_ok=True)
    prompt = out / "prompt.md"
    prompt.write_text(PROBE_PROMPT, encoding="utf-8")
    model = (provider.get("models") or {}).get(capability_class)
    request = AgentLaunchRequest(
        run_id="overhead", node_id=out.name, role="implementer", cwd=str(cwd), prompt_path=str(prompt),
        output_dir=str(out), capability_class=capability_class, effort="low", model=model,
        provider_effort=(provider.get("effort_map") or {}).get("low", "low"), read_only=False, timeout_seconds=int(timeout),
    )
    plan = adapter.resolve_invocation(request)
    started = time.monotonic()
    handle = adapter.start(request)
    while adapter.poll(handle).running:
        if time.monotonic() - started > timeout:
            adapter.cancel(handle)
            break
        time.sleep(0.5)
    result = adapter.collect(handle)
    return {
        "outcome": result.outcome,
        "failure_kind": result.failure_kind,
        "answer": (result.summary or "")[-80:],
        "seconds": round(time.monotonic() - started, 1),
        "usage": result.usage,
        "flags": [item for item in plan.argv if item.startswith("--") or item.startswith("-c")] + [item for item in plan.argv if item.startswith("mcp_") or "," in item],
    }


def measure(
    providers: list[str] | None = None,
    *,
    repository: str | Path = ".",
    capability_class: str = "fast",
    variants: list[str] | None = None,
    registry: ProviderRegistry | None = None,
    timeout: float = 300,
) -> dict[str, Any]:
    registry = registry or ProviderRegistry()
    repo = repository_root(Path(repository))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = orchestrator_home() / "overhead" / f"{stamp}-{uuid.uuid4().hex[:4]}"
    root.mkdir(parents=True, exist_ok=True)
    trees = _worktrees(repo, root, 2)
    report: dict[str, Any] = {"created_at": stamp, "repository": str(repo), "capability_class": capability_class, "prompt": PROBE_PROMPT.strip(), "providers": {}}
    try:
        for provider in registry.providers:
            if providers and provider["id"] not in providers:
                continue
            if not provider.get("enabled", True):
                continue
            rows = []
            for name, options in VARIANTS.get(provider.get("adapter"), []):
                if variants and name not in variants:
                    continue
                calls = [_probe(provider, options, tree, root / "calls" / f"{provider['id']}-{name}-{index}", capability_class, timeout) for index, tree in enumerate(trees)]
                rows.append({"variant": name, "options": options, "calls": calls, "summary": _summary(calls)})
            report["providers"][provider["id"]] = {"model": (provider.get("models") or {}).get(capability_class), "variants": rows}
    finally:
        for tree in trees:
            git(["worktree", "remove", "--force", str(tree)], repo, check=False)
    path = root / "overhead.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report["file"] = str(path)
    return report


def _summary(calls: list[dict[str, Any]]) -> dict[str, Any]:
    usable = [call["usage"] for call in calls if call["outcome"] == "completed" and (call["usage"] or {}).get("accuracy") == "exact"]
    if not usable:
        return {"ok": False, "reason": "; ".join(f"{call['failure_kind']}: {call['answer']}" for call in calls)[:300]}
    return {
        "ok": len(usable) == len(calls),
        "input_tokens_per_call": [item["input_tokens"] for item in usable],
        "cache_write_tokens_per_call": [item.get("cache_write_tokens") for item in usable],
        "uncached_input_tokens_per_call": [item.get("uncached_input_tokens") for item in usable],
        "output_tokens_per_call": [item.get("output_tokens") for item in usable],
        "cost_usd_per_call": [item.get("cost_usd") for item in usable],
    }
