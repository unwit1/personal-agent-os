from __future__ import annotations

import json
import subprocess
import unittest

from tests.readiness_fixtures import ReadinessFixture, git


class ReadinessFixtureTests(ReadinessFixture):
    def test_fixtures_are_clean_committed_repositories(self):
        self.assertEqual(set(self.fixtures), {'python', 'javascript'})
        for repo in self.fixtures.values():
            self.assertEqual(git(repo, 'branch', '--show-current').strip(), 'main')
            self.assertEqual(git(repo, 'status', '--porcelain'), '')
            self.assertEqual(git(repo, 'log', '-1', '--pretty=%s').strip(), 'init')
            self.assertFalse((repo / '.gitignore').exists())

    def test_python_fixture_layout_and_content(self):
        repo = self.py_repo
        self.assertIn("name = 'calc-fixture'", (repo / 'pyproject.toml').read_text(encoding='utf-8'))
        self.assertTrue((repo / 'calc' / '__init__.py').is_file())
        self.assertIn('return a + b', (repo / 'calc' / 'core.py').read_text(encoding='utf-8'))
        self.assertIn('add(1, 2), 3', (repo / 'tests' / 'test_core.py').read_text(encoding='utf-8'))

    def test_javascript_fixture_layout_and_content(self):
        repo = self.js_repo
        self.assertEqual(json.loads((repo / 'package.json').read_text(encoding='utf-8'))['scripts']['test'], 'node --test')
        self.assertIn('module.exports', (repo / 'src' / 'calc.js').read_text(encoding='utf-8'))
        test_source = (repo / 'test' / 'calc.test.js').read_text(encoding='utf-8')
        self.assertIn("require('node:test')", test_source)
        self.assertIn('add(1, 2), 3', test_source)

    def test_pass_and_synthetic_provider_helpers(self):
        self.assertEqual(self.engine, self)
        self.assertEqual(self.telemetry_path, self.tmp / 'telemetry' / 'events.jsonl')
        self.assertEqual(self.claims, self.tmp / 'claims.json')
        from tests.readiness_fixtures import PASS, provider
        self.assertEqual(PASS['kind'], 'command')
        self.assertEqual(provider('alpha')['adapter'], 'synthetic')


if __name__ == '__main__':
    unittest.main()
