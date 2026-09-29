"""Simplification engine, first deterministic slice (MIE-0011):
``agent-os orchestrate simplify``.

Builds a component view of ``src/agent_os`` and proposes candidates, deleting
nothing:

* per module: non-blank lines, importers (src and tests, from the import
  graph in test_selection.py), last change and 90-day churn from Git;
* **dead-module candidates**: no importers anywhere and not an entry point;
* **unused public functions**: a top-level public ``def`` whose name appears
  nowhere else in the repository (the name-usage heuristic of vulture,
  prior art PA-vulture; dynamic uses such as ``getattr`` or CLI strings make
  this a candidate list, not a verdict);
* **duplicate function bodies**: identical normalized ASTs (identifiers,
  constants and docstrings erased) across functions of >= 5 statements
  (the normalization idea of PA-pychase);
* **dependency use**: each runtime dependency in pyproject and where it is
  imported (removal candidates when unused);
* **prior-art matches**: large modules whose purpose matches a registry entry
  (replace/borrow candidates), consulting the registry as MIE-0011 requires.

Every persistent subsystem should be able to say why it exists, what it costs
and how to delete it (constitution section 11); this report is the evidence.
"""

from __future__ import annotations

import ast
import hashlib
import re
import subprocess
import tomllib
import warnings
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from ..paths import ROOT
from .test_selection import ImportGraphSelector

ENTRY_POINTS = {"agent_os", "agent_os.__main__", "agent_os.cli"}
MIN_DUPLICATE_STATEMENTS = 5
LARGE_MODULE_LINES = 400
REPORT = ROOT / "projects" / "personal-agent-os" / "orchestrator-os" / "simplification-report.json"


def _parse(source: str) -> ast.Module | None:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            return ast.parse(source)
    except SyntaxError:
        return None


class _Normalize(ast.NodeTransformer):
    """Erase local names, argument names and constant values; keep attribute
    and method names, which carry meaning (erasing them made x.sort() and
    x.reverse() look identical)."""

    def visit_Name(self, node: ast.Name) -> ast.AST:
        return ast.copy_location(ast.Name(id="_", ctx=node.ctx), node)

    def visit_arg(self, node: ast.arg) -> ast.AST:
        node.arg = "_"
        node.annotation = None
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        return ast.copy_location(ast.Constant(value=type(node.value).__name__), node)


def body_fingerprint(function: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    body = list(function.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    if sum(1 for _ in body for _ in [0]) < MIN_DUPLICATE_STATEMENTS:
        return None
    module = ast.Module(body=[_Normalize().visit(ast.parse(ast.unparse(statement))) for statement in body], type_ignores=[])
    return hashlib.sha256(ast.dump(module, annotate_fields=False).encode()).hexdigest()[:16]


def _git(args: list[str], root: Path) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout


def build(root: Path | None = None, *, churn_days: int = 90) -> dict[str, Any]:
    root = Path(root or ROOT)
    selector = ImportGraphSelector(None, root)
    modules = {module: path for path, module in selector.src.items()}
    importers: dict[str, set[str]] = defaultdict(set)
    for source_module, targets in selector.graph.items():
        for target in targets:
            if target != source_module:
                importers[target].add(source_module)
    test_importers: dict[str, set[str]] = defaultdict(set)
    for test, targets in selector.test_imports.items():
        for target in targets:
            test_importers[target].add(test)
    # Importing a.b.c imports a and a.b too: count parents as used.
    for module in list(importers) + list(test_importers):
        parts = module.split(".")
        for index in range(1, len(parts)):
            importers[".".join(parts[:index])].add(module)

    churn: dict[str, int] = defaultdict(int)
    for line in _git(["log", f"--since={churn_days}.days", "--name-only", "--format="], root).splitlines():
        if line.startswith("src/agent_os/") and line.endswith(".py"):
            churn[line] += 1

    corpus_files = [p for p in root.rglob("*.py") if ".agent-local" not in p.parts and "third_party" not in p.parts and ".git" not in p.parts]
    corpus = {p: p.read_text(encoding="utf-8", errors="replace") for p in corpus_files}
    words: dict[str, int] = defaultdict(int)
    for text in corpus.values():
        for word in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text):
            words[word] += 1
    for extra in list(root.glob("*.toml")) + list(root.glob("docs/**/*.md")):
        for word in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", extra.read_text(encoding="utf-8", errors="replace")):
            words[word] += 1

    components, unused, fingerprints = [], [], defaultdict(list)
    for module, rel in sorted(modules.items()):
        text = corpus.get(root / rel, "")
        tree = _parse(text)
        lines = sum(1 for line in text.splitlines() if line.strip())
        docstring = (ast.get_docstring(tree) or "").strip().splitlines()[0] if tree and ast.get_docstring(tree) else ""
        last = _git(["log", "-1", "--format=%cs", "--", rel], root).strip() or None
        components.append({"module": module, "path": rel, "lines": lines, "importers": sorted(importers.get(module, set()))[:12], "importer_count": len(importers.get(module, set())),
                           "tests": sorted(test_importers.get(module, set()))[:12], "test_count": len(test_importers.get(module, set())), "last_changed": last,
                           f"churn_{churn_days}d": churn.get(rel, 0), "purpose": docstring[:160]})
        if not tree:
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not node.name.startswith("_") and words.get(node.name, 0) <= 1 and not isinstance(node, ast.ClassDef):
                    unused.append({"module": module, "name": node.name, "line": node.lineno, "confidence": "medium (name appears only at its definition)"})
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fingerprint = body_fingerprint(node)
                if fingerprint:
                    fingerprints[fingerprint].append(f"{module}:{node.name}")
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        fingerprint = body_fingerprint(item)
                        if fingerprint:
                            fingerprints[fingerprint].append(f"{module}:{node.name}.{item.name}")

    dead_modules = [c for c in components if c["importer_count"] == 0 and c["test_count"] == 0 and c["module"] not in ENTRY_POINTS and not c["module"].endswith("__init__")]
    duplicates = [{"fingerprint": key, "functions": sorted(value)} for key, value in fingerprints.items() if len(value) > 1]

    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = []
    for requirement in pyproject.get("project", {}).get("dependencies", []):
        name = re.split(r"[<>=!~\[ ;]", requirement, maxsplit=1)[0].strip()
        import_name = name.replace("-", "_").lower()
        users = sorted(str(p.relative_to(root)).replace("\\", "/") for p, text in corpus.items() if re.search(rf"^\s*(?:import|from)\s+{re.escape(import_name)}\b", text, re.M) and p.is_relative_to(root / "src"))
        dependencies.append({"requirement": requirement, "imported_by": users[:10], "candidate": "remove" if not users else "keep"})

    prior_art = []
    try:
        from . import prior_art as registry

        loaded = registry.load()
        for component in components:
            if component["lines"] >= LARGE_MODULE_LINES and component["purpose"]:
                text = component["purpose"] + " " + component["module"].split(".")[-1]
                wanted = registry._terms(text)
                # Require overlap with the entry's capability areas (>= 2 terms),
                # not just shared generic words (same rule as prior_art.queries).
                matches = [m for m in registry.lookup(text, loaded, limit=6) if len(wanted & registry._terms(" ".join(m.get("capability_areas") or []))) >= 2][:3]
                if matches:
                    prior_art.append({"module": component["module"], "lines": component["lines"], "consider": [{"id": m["id"], "decision": m["decision"], "matched": m["matched"]} for m in matches]})
    except Exception as exc:  # the registry is advisory
        prior_art.append({"error": str(exc)[:160]})

    total = sum(c["lines"] for c in components)
    return {
        "schema": "personal-agent/simplification-report/v1", "generated_at": date.today().isoformat(),
        "totals": {"modules": len(components), "lines": total, "dead_module_candidates": len(dead_modules), "unused_public_functions": len(unused),
                   "duplicate_groups": len(duplicates), "prior_art_matches": len([p for p in prior_art if "module" in p])},
        "largest": sorted(({k: c[k] for k in ("module", "lines", "importer_count", "test_count", f"churn_{churn_days}d")} for c in components), key=lambda c: -c["lines"])[:10],
        "dead_module_candidates": dead_modules, "unused_public_functions": unused, "duplicates": duplicates,
        "dependencies": dependencies, "prior_art_matches": prior_art, "components": components,
        "notes": ["Candidates, not verdicts: dynamic imports, CLI dispatch strings, MCP tool names and plugin registries can hide real uses.", "Nothing is deleted by this command."],
    }


def write(report: dict[str, Any], path: Path | None = None) -> str:
    import json

    target = Path(path or REPORT)
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    return str(target)
