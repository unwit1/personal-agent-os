from __future__ import annotations

from pathlib import Path
from typing import Any

from .paths import ROOT
from .registry import projects


REPOSITORY_TOKEN = "{{AGENT_OS_REPOSITORY}}"


def render(text: str) -> str:
    """Resolve the checkout placeholder for this machine.

    Canonical adapter text in Git must stay machine-independent, or a clone on
    another computer instructs the agent to run a path that does not exist here.
    The concrete checkout belongs only in the copy written to the local client.
    """
    return text.replace(REPOSITORY_TOKEN, str(ROOT))


PROJECT_ADAPTERS = {
    "auto-click": "auto-click-AGENTS.md",
    "job-applicant-dashboard": "job-applicant-dashboard-AGENTS.md",
    "overtime-parser": "overtime-parser-AGENTS.md",
    "tes-tagger": "tes-tagger-AGENTS.md",
    "scan-renamer": "scan-renamer-AGENTS.md",
}


def targets() -> list[tuple[Path, Path]]:
    project_by_id = {item["id"]: item for item in projects()}
    result = [
        (ROOT / "adapters" / "global" / "AGENTS.md", Path.home() / ".codex" / "AGENTS.md"),
        (
            ROOT / ".agents" / "skills" / "personal-agent-os" / "SKILL.md",
            Path.home() / ".codex" / "skills" / "personal-agent-os" / "SKILL.md",
        ),
    ]
    for project_id, filename in PROJECT_ADAPTERS.items():
        result.append(
            (
                ROOT / "adapters" / "projects" / filename,
                Path(project_by_id[project_id]["path"]) / "AGENTS.md",
            )
        )
    return result


def status() -> list[dict[str, Any]]:
    result = []
    for source, destination in targets():
        source_text = render(source.read_text(encoding="utf-8"))
        exists = destination.exists()
        matches = exists and destination.read_text(encoding="utf-8") == source_text
        result.append(
            {
                "source": str(source),
                "destination": str(destination),
                "exists": exists,
                "matches": matches,
            }
        )
    return result


def install() -> dict[str, list[str]]:
    installed: list[str] = []
    unchanged: list[str] = []
    conflicts: list[str] = []
    for source, destination in targets():
        source_text = render(source.read_text(encoding="utf-8"))
        if destination.exists():
            if destination.read_text(encoding="utf-8") == source_text:
                unchanged.append(str(destination))
            else:
                conflicts.append(str(destination))
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source_text, encoding="utf-8", newline="\n")
        installed.append(str(destination))
    return {"installed": installed, "unchanged": unchanged, "conflicts": conflicts}
