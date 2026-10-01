from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from readiness_fixtures import ReadinessFixture, edit_script, provider
from agent_os.orchestrator.adapters import synthetic
from agent_os.orchestrator.engine import Orchestrator
from agent_os.orchestrator.model import DEFAULT_POLICY, PolicyError, merge_policy
from agent_os.orchestrator.router import ProviderRegistry
from agent_os.orchestrator.store import RunStore
from agent_os.telemetry import LocalTelemetryStore


class CostReadinessTests(ReadinessFixture):
    def setUp(self):
        super().setUp()
        self.engine = Orchestrator(
            RunStore(self.tmp / 'home'),
            registry=ProviderRegistry(providers=[provider(name) for name in self.providers]),
            telemetry_store=LocalTelemetryStore(self.telemetry_path),
            claims_path=self.claims,
            sleep=lambda seconds: None,
        )

    def policy(self, **overrides):
        return {'auto_continue': True, 'poll_interval_seconds': 0, 'announce_claims': False, **overrides}

    def task(self, task_id):
        return {'id': task_id, 'goal': f'work {task_id}', 'scope': [task_id], 'validators': [{'kind': 'command', 'command': [sys.executable, '-c', "print('ok')"]}]}

    def check_fixture(self, fixture_name, check):
        repo = self.fixtures[fixture_name]
        run_id = self.engine.create_run('cost readiness', repository=repo, tasks=check['tasks'], policy=self.policy(**check.get('policy', {})))['run_id']
        return run_id

    def test_CC1_launch_budget_stops_before_approval(self):
        for fixture in self.fixtures:
            with self.subTest(fixture=fixture):
                run = self.check_fixture(fixture, {'tasks': [self.task('a'), self.task('b')], 'policy': {'max_launches': 1}})
                stopped = self.engine.run_loop(run, max_ticks=30)
                record = self.engine.load(run)
                self.assertEqual(stopped['state'], 'APPROVAL_REQUIRED')
                self.assertEqual(stopped['gates'][-1]['kind'], 'budget_exhausted')
                self.assertLessEqual(record['launches'], 1)

    def test_CC2_run_usage_totals_exist(self):
        for fixture, repo in self.fixtures.items():
            with self.subTest(fixture=fixture):
                run = self.engine.create_run('usage readiness', repository=repo, tasks=[self.task('a')], policy=self.policy())['run_id']
                final = self.engine.run_loop(run, max_ticks=40)
                self.assertEqual(final['state'], 'COMPLETE')
                usage = self.engine.load(run)['usage']
                self.assertIsInstance(usage, dict)
                expected = {'input_tokens', 'cached_tokens', 'output_tokens', 'workers', 'cache_write_tokens', 'reasoning_tokens', 'cost_usd', 'calls_exact', 'calls_estimated', 'calls_unavailable'}
                self.assertTrue(expected.issubset(usage), f"missing usage keys: {expected - usage.keys()}")

    def test_CC3_out_of_usage_waits_without_looping(self):
        for fixture, repo in self.fixtures.items():
            with self.subTest(fixture=fixture):
                for name in self.providers:
                    synthetic.SCRIPTS[name] = edit_script({'a': {'failure': 'quota', 'detail': 'usage limit reached'}})
                run = self.engine.create_run('quota readiness', repository=repo, tasks=[self.task('a')], policy=self.policy())['run_id']
                stopped = self.engine.run_loop(run, max_ticks=40)
                self.assertIn(stopped['state'], {'READY', 'BLOCKED'})
                self.assertIn('usage', stopped['state_reason'].lower())

    def test_CC4_retries_and_escalation_are_bounded(self):
        for fixture, repo in self.fixtures.items():
            with self.subTest(fixture=fixture):
                synthetic.reset()
                for name in self.providers:
                    synthetic.SCRIPTS[name] = edit_script()
                failing = {'kind': 'command', 'command': [sys.executable, '-c', 'raise SystemExit(3)']}
                run = self.engine.create_run('retry readiness', repository=repo, tasks=[{**self.task('a'), 'validators': [failing]}], policy=self.policy(max_escalations=2))['run_id']
                final = self.engine.run_loop(run, max_ticks=40)
                node = self.engine.load(run)['nodes']['a']
                self.assertEqual(final['state'], 'BLOCKED')
                self.assertEqual(node['state'], 'FAILED_FINAL')
                self.assertEqual(node['escalations'], 2)
                self.assertEqual(node['attempts'], 3)

                for name in self.providers:
                    synthetic.SCRIPTS[name] = edit_script({'a': {'failure': 'process_error'}})
                run = self.engine.create_run('retry readiness', repository=repo, tasks=[self.task('a')], policy=self.policy(max_stage_retries=2, max_escalations=2))['run_id']
                final = self.engine.run_loop(run, max_ticks=40)
                node = self.engine.load(run)['nodes']['a']
                self.assertEqual(final['state'], 'BLOCKED')
                self.assertLessEqual(node['attempts'], 3)
                self.assertLessEqual(node['escalations'], 2)

    def test_CC5_unknown_money_cap_is_rejected(self):
        self.assertFalse(any(any(part in key for part in ('usd', 'token', 'cost', 'money')) for key in DEFAULT_POLICY))
        with self.assertRaises(PolicyError):
            merge_policy({'max_usd': 1})

    def test_CC6_synthetic_registry_only(self):
        for entry in self.engine.registry().providers:
            self.assertEqual(entry['adapter'], 'synthetic')
