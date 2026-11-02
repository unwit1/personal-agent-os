"""Build the standalone orchestrator-os tree from a personal-agent-os checkout.

Reproducible and idempotent: it only reads the source checkout and (re)writes
the destination directory. Nothing in the source is modified or deleted.

    python migrations/orchestrator-os-extraction/extract.py --dest ../orchestrator-os

What it does (and nothing else):
1. Copies src/agent_os/orchestrator/** to src/orchestrator_os/.
2. Vendors the six leaf utilities the engine needs (timestamps, storage,
   fingerprints, local_paths, telemetry, capabilities).
3. Rewrites every import of Agent OS business logic (paths, registry,
   machine, compiler, improvements, coordination, economy) to the single
   seam ``orchestrator_os.host``.
4. Copies the Orchestrator GUI assets (not the Executive window), the
   Orchestrator tests that do not exercise Agent OS surfaces, test fixtures,
   the policy (as a packaged default) and the overlay files in this directory.
5. Writes PROVENANCE.json mapping every destination file to its source path
   and the source commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1]
OVERLAY = HERE / "overlay"

SUPPORT = ("timestamps", "storage", "fingerprints", "local_paths", "telemetry", "capabilities")
HOST_MODULES = ("paths", "registry", "machine", "compiler", "improvements", "coordination")
ORCH_GUI = ("index.html", "app.js", "simple.js", "simple-core.js", "style.css")

# Tests that drive Agent OS's own CLI/MCP surfaces stay in Agent OS; they become
# the contract tests for the bridge.
AGENT_OS_SURFACE_TESTS = {
    "test_compute_provision_mcp.py",
    "test_orchestrator_surfaces.py",
    "test_orchestrator_host_actions.py",
}

POLICY_PATH_MAP = [
    ("src/agent_os/orchestrator/", "src/orchestrator_os/"),
    ("projects/personal-agent-os/orchestrator-os/", "state/orchestrator/"),
]
# Agent OS files that do not exist in this repository.
POLICY_DROP = {"src/agent_os/privacy.py"}

STATE_COPIES = [
    ("projects/personal-agent-os/orchestrator-os/evals", "state/orchestrator/evals"),
    ("projects/personal-agent-os/orchestrator-os/records", "state/orchestrator/records"),
    ("projects/personal-agent-os/orchestrator-os/provider-policy", "state/orchestrator/provider-policy"),
    ("projects/personal-agent-os/research/prior-art", "state/research/prior-art"),
    ("projects/personal-agent-os/research/meta-improvement/improvement-backlog.json",
     "state/research/meta-improvement/improvement-backlog.json"),
]

PATH_CONSTANTS = [
    (r'ROOT / "projects" / "personal-agent-os" / "orchestrator-os"', "OS_DIR"),
    (r'ROOT / "projects" / "personal-agent-os" / "research"', "RESEARCH_DIR"),
    (r'ROOT / "projects" / "personal-agent-os" / "improvements"', "IMPROVEMENTS_DIR"),
    (r'ROOT / "policy" / "orchestrator-os.policy.json"', "POLICY_PATH"),
    (r'ROOT / "projects/personal-agent-os/orchestrator-os/provider-policy/', 'PROVIDER_POLICY_DIR / "'),
    (r'ROOT / "gui"', "GUI_DIR"),
]


def rewrite_engine_module(text: str, depth: int) -> str:
    """Rewrite one module copied from agent_os/orchestrator.

    ``depth`` is 0 for top-level modules and 1 for adapters/*. Relative
    ``..x`` imports in top-level modules pointed at agent_os; in adapters they
    already point at the orchestrator package and stay as they are.
    """
    up = "." if depth == 0 else ".."
    parent = r"\.\." if depth == 0 else r"\.\.\."
    for name in SUPPORT:
        text = re.sub(rf"from {parent}{name} import", f"from {up}{name} import", text)
    for name in HOST_MODULES:
        text = re.sub(rf"from {parent}{name} import", f"from {up}host import", text)
    text = text.replace("from agent_os import economy", f"from {up} import host as _host")
    if "_host.economy" not in text and "from . import host as _host" in text:
        text = re.sub(r"\beconomy\.", "_host.economy().", text)
    for pattern, constant in PATH_CONSTANTS:
        if pattern in text:
            text = text.replace(pattern, constant)
            name = constant.split()[0]
            if not re.search(rf"from {re.escape(up)}host import [^\n]*\b{name}\b", text):
                text = _add_host_import(text, up, name)
    text = text.replace('str(ROOT / "agent.py"), "orchestrate", "run"', '"-m", "orchestrator_os", "run"')
    text = text.replace('{"agent_os", "agent_os.__main__", "agent_os.cli"}',
                        '{"orchestrator_os", "orchestrator_os.__main__", "orchestrator_os.cli"}')
    text = text.replace("agent_os.orchestrator", "orchestrator_os")
    # Repo-relative paths of the engine's own files (control-plane floor,
    # eval task corpus, worker guidance) now live under src/orchestrator_os.
    text = text.replace("src/agent_os/orchestrator/", "src/orchestrator_os/")
    text = text.replace("src/agent_os/orchestrator", "src/orchestrator_os")
    return text


def _add_host_import(text: str, up: str, name: str) -> str:
    line = f"from {up}host import {name}\n"
    match = re.search(r"^from __future__ import annotations\n", text, re.M)
    if match:
        return text[: match.end()] + "\n" + line + text[match.end():]
    return line + text


def rewrite_support_module(text: str) -> str:
    text = text.replace("from .paths import ROOT", "from .host import ROOT")
    text = text.replace("from .machine import CONFIG_DIR", "from .host import CONFIG_DIR")
    return text


TEST_REWRITES = [
    ("agent_os.orchestrator", "orchestrator_os"),
    ("from agent_os.telemetry import", "from orchestrator_os.telemetry import"),
    ("from agent_os.storage import", "from orchestrator_os.storage import"),
    ("from agent_os.timestamps import", "from orchestrator_os.timestamps import"),
    ("from agent_os.fingerprints import", "from orchestrator_os.fingerprints import"),
    ("from agent_os import capabilities", "from orchestrator_os import capabilities"),
    ("from agent_os.capabilities import", "from orchestrator_os.capabilities import"),
    ("from agent_os.paths import ROOT", "from orchestrator_os.host import ROOT"),
    ("import agent_os.paths", "import orchestrator_os.host"),
    ("agent_os.paths.ROOT", "orchestrator_os.host.ROOT"),
    ("from agent_os.cli import main", "from orchestrator_os.__main__ import main"),
    ('"agent_os.storage.', '"orchestrator_os.storage.'),
    ('"agent_os.capabilities.', '"orchestrator_os.capabilities.'),
    ('"agent_os.telemetry.', '"orchestrator_os.telemetry.'),
    ('"agent_os.timestamps', '"orchestrator_os.timestamps'),
    ("src/agent_os/orchestrator", "src/orchestrator_os"),
    ('"src" / "agent_os" / "orchestrator"', '"src" / "orchestrator_os"'),
    ('parents[1] / "src" / "agent_os"', 'parents[1] / "src" / "orchestrator_os"'),
    ('parents[1] / "gui"', 'parents[1] / "src" / "orchestrator_os" / "gui"'),
    # The repository's policy re-points the evidence tree (POLICY_PATH_MAP).
    ("projects/personal-agent-os/orchestrator-os/", "state/orchestrator/"),
]

# Orchestrator documentation (the executive-* pages describe the Agent OS
# Executive window and stay in Agent OS).
ORCH_DOCS = (
    "docs/multi-agent-orchestrator.md",
    "docs/orchestrator-os/COMMANDS.md",
    "docs/orchestrator-os/CONSTITUTION.md",
    "docs/orchestrator-os/ENTRYPOINT.md",
    "docs/orchestrator-os/readiness.md",
    "docs/orchestrator-os/readiness",
    "docs/orchestrator-os/self-audit.md",
    "docs/orchestrator-os/self-audit",
    "docs/orchestrator-os/roadmap-status-parsing.md",
    "docs/orchestrator-os/session-foreman-report.md",
    "docs/orchestrator-os/task-cache-route.md",
)


def is_orchestrator_test(text: str) -> bool:
    return bool(re.search(r"agent_os\.orchestrator|from agent_os import orchestrator", text))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dest", required=True, type=Path)
    args = parser.parse_args()
    dest: Path = args.dest.resolve()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=SOURCE, capture_output=True, text=True, check=True).stdout.strip()
    provenance: dict[str, str] = {}

    pkg = dest / "src" / "orchestrator_os"
    if pkg.exists():
        shutil.rmtree(pkg)
    if (dest / "tests").exists():
        shutil.rmtree(dest / "tests")
    pkg.mkdir(parents=True)

    engine_src = SOURCE / "src" / "agent_os" / "orchestrator"
    for path in sorted(engine_src.rglob("*")):
        if "__pycache__" in path.parts or path.is_dir():
            continue
        relative = path.relative_to(engine_src)
        target = pkg / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".py":
            depth = len(relative.parts) - 1
            target.write_text(rewrite_engine_module(path.read_text(encoding="utf-8"), min(depth, 1)), encoding="utf-8")
        else:
            shutil.copy2(path, target)
        provenance[target.relative_to(dest).as_posix()] = path.relative_to(SOURCE).as_posix()

    for name in SUPPORT:
        path = SOURCE / "src" / "agent_os" / f"{name}.py"
        target = pkg / f"{name}.py"
        target.write_text(rewrite_support_module(path.read_text(encoding="utf-8")), encoding="utf-8")
        provenance[target.relative_to(dest).as_posix()] = path.relative_to(SOURCE).as_posix()

    (pkg / "gui").mkdir()
    for name in ORCH_GUI:
        shutil.copy2(SOURCE / "gui" / name, pkg / "gui" / name)
        provenance[f"src/orchestrator_os/gui/{name}"] = f"gui/{name}"

    (pkg / "defaults").mkdir()
    shutil.copy2(SOURCE / "policy" / "orchestrator-os.policy.json", pkg / "defaults" / "orchestrator-os.policy.json")
    provenance["src/orchestrator_os/defaults/orchestrator-os.policy.json"] = "policy/orchestrator-os.policy.json"
    shutil.copytree(SOURCE / "projects/personal-agent-os/orchestrator-os/provider-policy", pkg / "defaults" / "provider-policy")
    provenance["src/orchestrator_os/defaults/provider-policy/"] = "projects/personal-agent-os/orchestrator-os/provider-policy/"

    # The repository's own control-plane policy: same rules, paths re-pointed
    # at this repository's layout. Agent OS keeps its copy for its own runs.
    policy_text = (SOURCE / "policy" / "orchestrator-os.policy.json").read_text(encoding="utf-8")
    for old, new in POLICY_PATH_MAP:
        policy_text = policy_text.replace(old, new)
    policy = json.loads(policy_text)
    protected = policy["control_plane"]["protected_paths"]
    policy["control_plane"]["protected_paths"] = [item for item in protected if item not in POLICY_DROP]
    (dest / "policy").mkdir(exist_ok=True)
    (dest / "policy" / "orchestrator-os.policy.json").write_text(json.dumps(policy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    provenance["policy/orchestrator-os.policy.json"] = "policy/orchestrator-os.policy.json (paths re-pointed)"

    tests = dest / "tests"
    tests.mkdir()
    skipped = []
    for path in sorted((SOURCE / "tests").glob("test_*.py")):
        text = path.read_text(encoding="utf-8")
        if not is_orchestrator_test(text):
            continue
        if path.name in AGENT_OS_SURFACE_TESTS:
            skipped.append(path.name)
            continue
        for old, new in TEST_REWRITES:
            text = text.replace(old, new)
        (tests / path.name).write_text(text, encoding="utf-8")
        provenance[f"tests/{path.name}"] = f"tests/{path.name}"
    for helper in ("readiness_fixtures.py",):
        text = (SOURCE / "tests" / helper).read_text(encoding="utf-8")
        for old, new in TEST_REWRITES:
            text = text.replace(old, new)
        (tests / helper).write_text(text, encoding="utf-8")
        provenance[f"tests/{helper}"] = f"tests/{helper}"
    if (SOURCE / "tests" / "gui").exists():
        shutil.copytree(SOURCE / "tests" / "gui", tests / "gui", ignore=shutil.ignore_patterns("__pycache__", "node_modules"))
        provenance["tests/gui/"] = "tests/gui/"
    if (dest / "docs").exists():
        shutil.rmtree(dest / "docs")
    for item in ORCH_DOCS:
        source, target = SOURCE / item, dest / item
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
        provenance[item + ("/" if source.is_dir() else "")] = item + ("/" if source.is_dir() else "")
    if (SOURCE / "tests" / "fixtures").exists():
        shutil.copytree(SOURCE / "tests" / "fixtures", tests / "fixtures", ignore=shutil.ignore_patterns("__pycache__"))
        provenance["tests/fixtures/"] = "tests/fixtures/"

    # Orchestrator-owned evidence moves with the code (append-only history is
    # preserved byte for byte). Checkpoints, status and next-prompt stay in
    # Agent OS: they interleave Agent OS feature work and are its session history.
    if (dest / "state").exists():
        shutil.rmtree(dest / "state")
    for source_rel, target_rel in STATE_COPIES:
        source, target = SOURCE / source_rel, dest / target_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy2(source, target)
        provenance[target_rel] = source_rel

    for path in sorted(OVERLAY.rglob("*")):
        if path.is_dir() or "__pycache__" in path.parts:
            continue
        target = dest / path.relative_to(OVERLAY)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        provenance.setdefault(target.relative_to(dest).as_posix(), "new (migrations/orchestrator-os-extraction/overlay)")

    record = {
        "schema": "orchestrator-os/provenance/v1",
        "source_repository": "https://github.com/unwit1/personal-agent-os",
        "source_commit": commit,
        "method": "copy + mechanical import rewrite (migrations/orchestrator-os-extraction/extract.py); history not rewritten",
        "agent_os_surface_tests_left_in_source": sorted(skipped),
        "files": dict(sorted(provenance.items())),
    }
    (dest / "PROVENANCE.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    leftovers = [p.relative_to(dest).as_posix() for p in pkg.rglob("*.py")
                 if re.search(r"from \.\.(paths|registry|machine|compiler|improvements|coordination)\b|\bagent_os\b(?!_)", p.read_text(encoding="utf-8"))]
    print(json.dumps({"dest": str(dest), "files": len(provenance), "source_commit": commit, "agent_os_references_left": leftovers}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
