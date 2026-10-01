"""Disposable Python and JavaScript repositories for readiness checks."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from agent_os.orchestrator.adapters import synthetic
from agent_os.orchestrator.adapters.base import AgentLaunchRequest


PASS = {'kind': 'command', 'command': [sys.executable, '-c', "print('ok')"]}


def git(repo, *args):
    return subprocess.run(
        ['git', '-c', 'user.name=fixture', '-c', 'user.email=f@x', *args],
        cwd=repo, check=True, capture_output=True, text=True,
    ).stdout


def make_python_fixture(root: Path) -> Path:
    repo = root / 'py-fixture'
    repo.mkdir()
    git(repo, 'init', '-b', 'main')
    (repo / 'pyproject.toml').write_text(
        "[project]\nname = 'calc-fixture'\nversion = '0.0.1'\n", encoding='utf-8'
    )
    (repo / 'calc').mkdir()
    (repo / 'calc' / '__init__.py').write_text('', encoding='utf-8')
    (repo / 'calc' / 'core.py').write_text('def add(a, b):\n    return a + b\n', encoding='utf-8')
    (repo / 'tests').mkdir()
    (repo / 'tests' / 'test_core.py').write_text(
        'import unittest\n\nfrom calc.core import add\n\n\n'
        'class AddTests(unittest.TestCase):\n'
        '    def test_add(self):\n        self.assertEqual(add(1, 2), 3)\n',
        encoding='utf-8',
    )
    (repo / 'README.md').write_text('# Python fixture\n', encoding='utf-8')
    git(repo, 'add', '-A')
    git(repo, 'commit', '-m', 'init')
    return repo


def make_javascript_fixture(root: Path) -> Path:
    repo = root / 'js-fixture'
    repo.mkdir()
    git(repo, 'init', '-b', 'main')
    (repo / 'package.json').write_text(
        json.dumps({'name': 'calc-fixture', 'version': '0.0.1', 'scripts': {'test': 'node --test'}}) + '\n',
        encoding='utf-8',
    )
    (repo / 'src').mkdir()
    (repo / 'src' / 'calc.js').write_text(
        'module.exports = { add: (a, b) => a + b };\n', encoding='utf-8'
    )
    (repo / 'test').mkdir()
    (repo / 'test' / 'calc.test.js').write_text(
        "const { test } = require('node:test');\n"
        "const assert = require('node:assert');\n"
        "const { add } = require('../src/calc');\n\n"
        "test('adds two numbers', () => {\n"
        '  assert.strictEqual(add(1, 2), 3);\n});\n',
        encoding='utf-8',
    )
    (repo / 'README.md').write_text('# JavaScript fixture\n', encoding='utf-8')
    git(repo, 'add', '-A')
    git(repo, 'commit', '-m', 'init')
    return repo


def provider(provider_id: str, **extra) -> dict:
    entry = {
        "id": provider_id,
        "adapter": "synthetic",
        "models": {
            "fast": f"{provider_id}-fast",
            "balanced": f"{provider_id}-balanced",
            "reasoning": f"{provider_id}-reasoning",
            "frontier": f"{provider_id}-frontier",
        },
        "effort_map": {"none": "minimal", "low": "lo", "medium": "med", "high": "hi"},
        "max_concurrency": 2,
    }
    entry.update(extra)
    return entry


def edit_script(extra: dict | None = None):
    """Implementers write one file inside their first scope entry; reviewers approve."""

    def script(request: AgentLaunchRequest, call: int) -> dict:
        if request.role == "reviewer":
            return {"structured": {"status": "done", "verdict": "approved", "findings": []}}
        if request.role == "planner":
            return {"structured": {"status": "done", "tasks": [{"id": "impl", "goal": "do it", "scope": ["impl"]}]}}
        base = request.node_id.split(".")[0]
        behaviour = {"edits": {f"{base}/{request.node_id}-{call}.txt": "change\n"}, "structured": {"status": "done", "summary": "edited"}}
        behaviour.update((extra or {}).get(base, {}))
        return behaviour

    return script


class ReadinessFixture(unittest.TestCase):
    providers = ('alpha', 'beta')

    def setUp(self) -> None:
        synthetic.reset()
        self.tmp = Path(tempfile.mkdtemp(prefix='agent-os-readiness-'))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.addCleanup(synthetic.reset)
        self.py_repo = make_python_fixture(self.tmp)
        self.js_repo = make_javascript_fixture(self.tmp)
        self.fixtures = {'python': self.py_repo, 'javascript': self.js_repo}
        self.telemetry_path = self.tmp / 'telemetry' / 'events.jsonl'
        self.claims = self.tmp / 'claims.json'
        self.engine = self
        for name in self.providers:
            synthetic.SCRIPTS[name] = edit_script()
