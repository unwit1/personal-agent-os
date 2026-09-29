"""Mutation testing for control-plane modules: ``agent-os orchestrate mutate``.

Subsumed rather than depended on (DEC-0012): mutmut, the reference tool
(prior art PA-mutmut), refuses to run on native Windows ("please use the
WSL", upstream issue #397), and the operator prefers subsuming. This is a
small AST mutator with classic operators:

* comparison flips (== <-> !=, < <-> >=, <= <-> >, in <-> not in, is <-> is not)
* boolean operator swap (and <-> or), dropping a ``not``
* constant flips (True <-> False, n -> n+1 for small ints)
* ``return X`` -> ``return None``; an ``if`` test forced to True/False

Each mutant is written into a detached, throwaway worktree of the trusted
repository (never the checkout, so protected files are not touched), the
named test modules run, and the mutant is *killed* when they fail. Surviving
mutants point at logic the tests do not pin down. FND-0008 showed why this
matters: a vacuous invariant stayed green until a planted mutation exposed it.
"""

from __future__ import annotations

import ast
import copy
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

COMPARE_SWAP = {ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Lt: ast.GtE, ast.GtE: ast.Lt, ast.Gt: ast.LtE, ast.LtE: ast.Gt,
                ast.In: ast.NotIn, ast.NotIn: ast.In, ast.Is: ast.IsNot, ast.IsNot: ast.Is}


@dataclass
class Mutant:
    index: int
    line: int
    operator: str
    description: str
    source: str


class _Site(ast.NodeVisitor):
    """Collect (node path, operator) mutation sites in document order."""

    def __init__(self) -> None:
        self.sites: list[tuple[int, str, str]] = []  # (node id order, operator, description)
        self.order: list[ast.AST] = []

    def generic_visit(self, node: ast.AST) -> None:
        self.order.append(node)
        super().generic_visit(node)


def _docstring_nodes(tree: ast.AST) -> set[int]:
    skip = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), ast.Constant) and isinstance(first.value.value, str):
                skip.add(id(first.value))
    return skip


def _candidates(node: ast.AST) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if isinstance(node, ast.Compare):
        for position, op in enumerate(node.ops):
            if type(op) in COMPARE_SWAP:
                out.append((f"compare:{position}", f"{type(op).__name__} -> {COMPARE_SWAP[type(op)].__name__}"))
    elif isinstance(node, ast.BoolOp):
        out.append(("boolop", "and <-> or"))
    elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        out.append(("drop_not", "drop not"))
    elif isinstance(node, ast.Constant) and isinstance(node.value, bool):
        out.append(("bool_const", f"{node.value} -> {not node.value}"))
    elif isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool) and abs(node.value) < 1000:
        out.append(("int_const", f"{node.value} -> {node.value + 1}"))
    elif isinstance(node, ast.Return) and node.value is not None and not (isinstance(node.value, ast.Constant) and node.value.value is None):
        out.append(("return_none", "return value -> None"))
    elif isinstance(node, ast.If):
        out.append(("if_true", "if test -> True"))
        out.append(("if_false", "if test -> False"))
    return out


def _apply(node: ast.AST, operator: str) -> None:
    if operator.startswith("compare:"):
        position = int(operator.split(":")[1])
        node.ops[position] = COMPARE_SWAP[type(node.ops[position])]()
    elif operator == "boolop":
        node.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
    elif operator == "bool_const":
        node.value = not node.value
    elif operator == "int_const":
        node.value = node.value + 1
    elif operator == "return_none":
        node.value = ast.Constant(value=None)
    elif operator == "if_true":
        node.test = ast.Constant(value=True)
    elif operator == "if_false":
        node.test = ast.Constant(value=False)


def mutants(source: str, *, only_functions: set[str] | None = None) -> Iterator[Mutant]:
    tree = ast.parse(source)
    skip = _docstring_nodes(tree)
    index = 0
    walker = _Site()
    walker.visit(tree)
    for position, node in enumerate(walker.order):
        if id(node) in skip:
            continue
        if only_functions is not None:
            owner = _owner(tree, node)
            if owner not in only_functions:
                continue
        for operator, description in _candidates(node):
            if operator == "drop_not":
                mutated_tree = copy.deepcopy(tree)
                target = _Site()
                target.visit(mutated_tree)
                victim = target.order[position]
                parent = _parent(mutated_tree, victim)
                if parent is None:
                    continue
                _replace_child(parent, victim, victim.operand)
            else:
                mutated_tree = copy.deepcopy(tree)
                target = _Site()
                target.visit(mutated_tree)
                _apply(target.order[position], operator)
            try:
                mutated = ast.unparse(ast.fix_missing_locations(mutated_tree))
            except Exception:
                continue
            index += 1
            yield Mutant(index, getattr(node, "lineno", 0), operator.split(":")[0], description, mutated)


def _owner(tree: ast.AST, target: ast.AST) -> str | None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(node):
                if child is target:
                    return node.name
    return None


def _parent(tree: ast.AST, target: ast.AST) -> ast.AST | None:
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            if child is target:
                return node
    return None


def _replace_child(parent: ast.AST, old: ast.AST, new: ast.AST) -> None:
    for field, value in ast.iter_fields(parent):
        if value is old:
            setattr(parent, field, new)
            return
        if isinstance(value, list):
            for position, item in enumerate(value):
                if item is old:
                    value[position] = new
                    return


def run(module_path: str, test_modules: list[str], *, ref: str = "HEAD", only_functions: set[str] | None = None, workers: int = 4, timeout: int = 300, limit: int | None = None) -> dict[str, Any]:
    """Mutate ``module_path`` (repo-relative) in throwaway worktrees at ``ref``
    and run ``test_modules`` against each mutant."""
    from .eval import Worktree, resolve_commit

    commit = resolve_commit(ref)
    from ..paths import ROOT

    source = subprocess.run(["git", "show", f"{commit}:{module_path}"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True).stdout
    items = list(mutants(source, only_functions=only_functions))
    if limit is not None:
        items = items[:limit]
    started = time.monotonic()
    trees: list[Path] = []
    contexts = [Worktree(commit) for _ in range(max(1, min(workers, len(items) or 1)))]
    try:
        for context in contexts:
            trees.append(context.__enter__())
        baseline = subprocess.run([sys.executable, "-m", "unittest", *test_modules], cwd=trees[0], capture_output=True, text=True, timeout=timeout)
        if baseline.returncode != 0:
            return {"error": "tests fail on the unmutated code", "detail": (baseline.stdout + baseline.stderr)[-600:]}

        def one(pair: tuple[int, Mutant]) -> dict[str, Any]:
            slot, mutant = pair
            tree = trees[slot % len(trees)]
            target = tree / module_path
            original = target.read_text(encoding="utf-8")
            target.write_text(mutant.source, encoding="utf-8")
            try:
                result = subprocess.run([sys.executable, "-m", "unittest", *test_modules], cwd=tree, capture_output=True, text=True, timeout=timeout)
                status = "survived" if result.returncode == 0 else "killed"
            except subprocess.TimeoutExpired:
                status = "killed"  # a hang is a detected change
            finally:
                target.write_text(original, encoding="utf-8")
            return {"index": mutant.index, "line": mutant.line, "operator": mutant.operator, "description": mutant.description, "status": status}

        # One worker per worktree slot keeps mutants from overwriting each other.
        groups = [[(slot, item) for position, item in enumerate(items) if position % len(trees) == slot] for slot in range(len(trees))]
        with ThreadPoolExecutor(max_workers=len(trees)) as pool:
            results = [row for batch in pool.map(lambda group: [one(pair) for pair in group], groups) for row in batch]
    finally:
        for context in contexts:
            context.__exit__(None, None, None)
    results.sort(key=lambda row: row["index"])
    killed = sum(1 for row in results if row["status"] == "killed")
    return {"module": module_path, "ref": commit[:12], "tests": test_modules, "mutants": len(results), "killed": killed,
            "score": round(killed / len(results), 3) if results else None, "seconds": round(time.monotonic() - started, 1),
            "survivors": [row for row in results if row["status"] == "survived"]}
