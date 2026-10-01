from __future__ import annotations

import shutil
import sys
import unittest
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from readiness_fixtures import ReadinessFixture, edit_script, provider
from agent_os.orchestrator.adapters import synthetic
from agent_os.orchestrator.engine import Orchestrator, _project_commands
from agent_os.orchestrator.router import ProviderRegistry
from agent_os.orchestrator.store import RunStore
from agent_os.telemetry import LocalTelemetryStore


class ValidatorDetectionTests(ReadinessFixture):
    def setUp(self):
        super().setUp()
        self.engine = Orchestrator(
            RunStore(self.tmp / 'home'),
            registry=ProviderRegistry(providers=[provider('alpha'), provider('beta')]),
            telemetry_store=LocalTelemetryStore(self.telemetry_path),
            claims_path=self.claims,
            sleep=lambda seconds: None,
        )

    def run_task(self, repo, validators):
        result = self.engine.create_run(
            'validate fixture', repository=repo,
            tasks=[{'id': 'impl', 'goal': 'small fixture change', 'scope': ['impl'], 'validators': validators}],
            policy={'auto_continue': True, 'poll_interval_seconds': 0, 'announce_claims': False,
                    'require_distinct_review_provider': False, 'max_escalations': 0},
        )
        run_id = result['run_id']
        final = self.engine.run_loop(run_id, max_ticks=30)
        return run_id, final, self.engine.load(run_id)

    def test_vd1_unregistered_fixtures_have_no_default_validators(self):
        for name, repo in self.fixtures.items():
            with self.subTest(fixture=name):
                run_id = self.engine.create_run(
                    'inspect validators', repository=repo, tasks=None,
                    policy={'planning': 'single'},
                )['run_id']
                record = self.engine.load(run_id)
                self.assertEqual(record['policy']['default_validators'], [])
                self.assertEqual(len(record['nodes']), 1)
                self.assertEqual(next(iter(record['nodes'].values()))['validators'], [])

    def test_vd2_no_project_commands_without_registration(self):
        self.assertEqual(_project_commands(None), [])

    def test_vd3_explicit_javascript_validator_runs_from_worker_worktree(self):
        cwd_file = self.tmp / 'validator-cwd.txt'
        validator = {'kind': 'command', 'command': [sys.executable, '-c',
            "import json,os,sys; from pathlib import Path; "
            f"Path({str(cwd_file)!r}).write_text(os.getcwd(), encoding='utf-8'); "
            "sys.exit(0 if 'test' in json.load(open('package.json'))['scripts'] else 1)"]}
        run_id, final, record = self.run_task(self.js_repo, [validator])
        node = record['nodes']['impl']
        self.assertEqual(final['state'], 'COMPLETE', final.get('state_reason'))
        self.assertTrue(node['validation']['passed'], node['validation'])
        self.assertNotEqual(Path(node['worktree']['path']).resolve(), self.js_repo.resolve())
        self.assertEqual(Path(cwd_file.read_text(encoding='utf-8')).resolve(), Path(node['worktree']['path']).resolve())

    @unittest.skipUnless(shutil.which('node'), 'node not installed')
    def test_vd4_node_test_command_on_javascript_fixture(self):
        # Node's default isolated test runner cannot spawn child processes in
        # this Windows worker. Keep the requested command and disable test-file
        # isolation through Node's supported environment option.
        old_node_options = os.environ.get('NODE_OPTIONS')
        os.environ['NODE_OPTIONS'] = ' '.join(filter(None, [old_node_options, '--test-isolation=none']))
        try:
            run_id, final, record = self.run_task(self.js_repo, [{'kind': 'command', 'command': ['node', '--test']}])
        finally:
            if old_node_options is None:
                os.environ.pop('NODE_OPTIONS', None)
            else:
                os.environ['NODE_OPTIONS'] = old_node_options
        self.assertEqual(final['state'], 'COMPLETE', final.get('state_reason'))
        self.assertTrue(record['nodes']['impl']['validation']['passed'])

    def test_vd5_failing_javascript_validator_fails_validation(self):
        run_id, final, record = self.run_task(self.js_repo, [{'kind': 'command', 'command': [sys.executable, '-c', 'raise SystemExit(1)']}])
        node = record['nodes']['impl']
        self.assertNotEqual(final['state'], 'COMPLETE')
        self.assertEqual(node['state'], 'FAILED_FINAL')
        self.assertFalse(node['validation']['passed'])


if __name__ == '__main__':
    unittest.main()
