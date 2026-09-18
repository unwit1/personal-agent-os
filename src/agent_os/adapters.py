from __future__ import annotations

from .paths import ROOT


ADAPTER = """# Generated adapter — canonical source: policy/CANONICAL_AGENT_POLICY.md

Before meaningful work, run `agent-os context <project> \"<task>\"` and follow the
target project's local policy. Load only matched context and skills. Preserve
unrelated work, run deterministic validation first, and create a compact handoff
after material changes. Durable policy lives in `policy/CANONICAL_AGENT_POLICY.md`.
"""


def sync_adapters() -> list[str]:
    written = []
    for name in ("AGENTS.md", "CLAUDE.md"):
        path = ROOT / name
        path.write_text(ADAPTER, encoding="utf-8", newline="\n")
        written.append(str(path))
    return written
