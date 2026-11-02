"""Deterministic affected-test selection from the static import graph (IMP-0006).

EXP-0002 (EVR-0007) measured this selector against models on test-selection
cases with traced labels: recall 0.98 at zero model cost, selecting ~14 of 46
modules, matching the workhorse model and beating cheap ones. The engine uses
it to run the affected test modules first on intermediate nodes, so a failing
attempt fails fast; the full declared validators still run afterwards and
still gate completion, so no gate is weakened.

The selector is runtime code (the candidate); ``eval.py`` imports it and stays
the protected evaluator.
"""

from __future__ import annotations

import ast
import subprocess
import warnings
from pathlib import Path
from typing import Any, Callable

UNITTEST_MARKERS = ("unittest discover", "unittest", "pytest")


def module_imports(source: str, module_name: str, roots: set[str] | frozenset[str] | None = None) -> set[str]:
    """First-party modules imported by a module's source (absolute and relative).

    ``roots`` are the repository's top-level package names (from ``src/``).
    Without them, the module's own top-level package is the only root, and
    relative imports always count.
    """
    roots = set(roots) if roots else {module_name.split(".", 1)[0]}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(source)
    except SyntaxError:
        return set()
    package = module_name.rsplit(".", 1)[0]
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found |= {alias.name for alias in node.names if alias.name.split(".", 1)[0] in roots}
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                parts = package.split(".")
                base = ".".join(parts[: len(parts) - node.level + 1])
                target = f"{base}.{node.module}" if node.module else base
            else:
                target = node.module or ""
            if node.level or target.split(".", 1)[0] in roots:
                found.add(target)
                found |= {f"{target}.{alias.name}" for alias in node.names}
    return found


def _git_reader(repo: Path, commit: str) -> tuple[list[str], Callable[[str], str]]:
    def run(args: list[str]) -> str:
        return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL).stdout

    names = run(["ls-tree", "-r", "--name-only", commit, "src", "tests"]).splitlines()
    return names, lambda path: run(["show", f"{commit}:{path}"])


def _tree_reader(repo: Path) -> tuple[list[str], Callable[[str], str]]:
    names = [path.relative_to(repo).as_posix() for root in ("src", "tests") if (repo / root).is_dir() for path in (repo / root).rglob("*.py")]
    return names, lambda path: (repo / path).read_text(encoding="utf-8", errors="replace")


class ImportGraphSelector:
    """Select test modules whose transitive first-party import closure contains a
    changed module. ``commit`` reads sources from Git; ``commit=None`` reads
    the working tree of ``repo`` (a node's worktree)."""

    def __init__(self, commit: str | None, repo: Path | str | None = None) -> None:
        from .host import ROOT

        self.repo = Path(repo or ROOT)
        names, read = _git_reader(self.repo, commit) if commit else _tree_reader(self.repo)
        # Every package under src/ is first-party (src layout), whatever it is named.
        self.src = {name: self._module(name) for name in names if name.startswith("src/") and name.count("/") >= 2 and name.endswith(".py")}
        self.roots = frozenset(module.split(".", 1)[0] for module in self.src.values())
        tests = [name for name in names if name.startswith("tests/") and Path(name).name.startswith("test_") and name.endswith(".py") and name.count("/") == 1]
        known = set(self.src.values())
        self.graph = {module: {item for item in module_imports(read(path), module, self.roots) if item in known} for path, module in self.src.items()}
        self.test_imports = {f"tests.{Path(path).stem}": {item for item in module_imports(read(path), "tests.x", self.roots) if item in known} for path in tests}
        self._closures: dict[str, set[str]] = {}

    @staticmethod
    def _module(path: str) -> str:
        module = path[len("src/"):-3].replace("/", ".")
        return module[: -len(".__init__")] if module.endswith(".__init__") else module

    def _closure(self, module: str) -> set[str]:
        if module not in self._closures:
            seen, stack = set(), [module]
            while stack:
                current = stack.pop()
                if current in seen:
                    continue
                seen.add(current)
                parts = current.split(".")
                stack += [".".join(parts[:index]) for index in range(1, len(parts))]  # importing a.b.c runs a and a.b
                stack += list(self.graph.get(current, ()))
            self._closures[module] = seen
        return self._closures[module]

    def select(self, changed_files: list[str]) -> list[str]:
        changed = {self._module(path) for path in changed_files if path in self.src}
        # A changed test module is always affected.
        chosen = {f"tests.{Path(path).stem}" for path in changed_files if path.startswith("tests/test_") and path.endswith(".py") and f"tests.{Path(path).stem}" in self.test_imports}
        for test, imports in self.test_imports.items():
            reach = set().union(*(self._closure(item) for item in imports)) if imports else set()
            if reach & changed:
                chosen.add(test)
        return sorted(chosen)


def runs_unit_tests(validators: list[dict[str, Any]]) -> bool:
    """True when a declared validator runs the project's Python test suite."""
    for validator in validators:
        command = validator.get("command")
        text = command if isinstance(command, str) else " ".join(str(item) for item in command or [])
        if validator.get("kind") == "command" and "unittest" in text:
            return True
    return False


def affected_first_validator(changed_files: list[str], worktree: Path | str, python: str) -> dict[str, Any] | None:
    """A command validator for the affected test modules, or None when nothing
    is selected (no src/ packages in the tree, or no affected module)."""
    try:
        selector = ImportGraphSelector(None, worktree)
    except OSError:
        return None
    modules = selector.select(changed_files)
    if not modules or not selector.test_imports:
        return None
    return {"kind": "command", "name": "affected-tests", "command": [python, "-m", "unittest", *modules], "selected": modules, "of": len(selector.test_imports)}
