from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from readiness_fixtures import ReadinessFixture, git, provider
from agent_os.orchestrator.adapters import synthetic
from agent_os.orchestrator.engine import Orchestrator
from agent_os.orchestrator.store import RunStore
from agent_os.orchestrator.router import ProviderRegistry
from agent_os.telemetry import LocalTelemetryStore


class ReviewReadinessTests(ReadinessFixture):
    def setUp(self):
        super().setUp()
        self.repo = self.py_repo
        self.engine = Orchestrator(
            RunStore(self.tmp / 'home'),
            registry=ProviderRegistry(providers=[provider('alpha'), provider('beta')]),
            telemetry_store=LocalTelemetryStore(self.telemetry_path),
            claims_path=self.claims,
            sleep=lambda seconds: None,
        )
        for name in ('alpha', 'beta'):
            synthetic.SCRIPTS[name] = self.script

    def script(self, request, call):
        if request.role == 'reviewer':
            return {'structured': {'status': 'done', 'verdict': 'approved', 'findings': []}}
        return {'edits': {'a/impl.txt': 'impl\n'}, 'structured': {'status': 'done'}}

    def for_each_fixture(self, callback):
        for name, repo in self.fixtures.items():
            with self.subTest(fixture=name):
                self.repo = repo
                self.engine = Orchestrator(
                    RunStore(self.tmp / f'home-{name}'),
                    registry=ProviderRegistry(providers=[provider('alpha'), provider('beta')]),
                    telemetry_store=LocalTelemetryStore(self.tmp / f'telemetry-{name}' / 'events.jsonl'),
                    claims_path=self.tmp / f'claims-{name}.json',
                    sleep=lambda seconds: None,
                )
                synthetic.SCRIPTS['alpha'] = self.script
                synthetic.SCRIPTS['beta'] = self.script
                callback()

    def git_repo(self, repo, *args):
        return subprocess.run(['git', '-c', 'user.name=fixture', '-c', 'user.email=f@x', *args], cwd=repo, check=True, capture_output=True, text=True).stdout

    def task(self, **extra):
        value = {'id': 'a', 'goal': 'work', 'scope': ['a'], 'validators': [{'kind': 'command', 'command': [sys.executable, '-c', "print('ok')"]}]}
        value.update(extra)
        return value

    def create(self, **policy):
        base = {'auto_continue': True, 'poll_interval_seconds': 0, 'announce_claims': False}
        base.update(policy)
        return self.engine.create_run('readiness review', repository=self.repo, tasks=[self.task()], policy=base)['run_id']

    def test_cross_review_is_structured_and_material_findings_route_to_repair(self):
        def check():
            state = {'round': 0}
            finding = {'id': '1', 'severity': 'high', 'path': 'a/impl.txt', 'summary': 'missing null check', 'evidence': 'line 1', 'recommended_action': 'add a guard'}
            def script(request, call):
                if request.role == 'reviewer':
                    item = [{'status': 'done', 'verdict': 'changes_requested', 'findings': [finding]}, {'status': 'done', 'verdict': 'approved', 'findings': []}][min(state['round'], 1)]
                    state['round'] += 1
                    return {'structured': item}
                if request.role == 'repairer':
                    return {'edits': {'a/fixed.txt': 'fixed\n'}, 'structured': {'status': 'done', 'dispositions': [{'id': 'R1-1', 'disposition': 'fixed'}]}}
                return {'edits': {'a/impl.txt': 'impl\n'}, 'structured': {'status': 'done'}}
            synthetic.SCRIPTS['alpha'] = synthetic.SCRIPTS['beta'] = script
            run = self.create()
            final = self.engine.run_loop(run, max_ticks=60)
            self.assertEqual(final['state'], 'COMPLETE', final['state_reason'])
            node = self.engine.load(run)['nodes']['a']
            self.assertEqual(node['review']['rounds'], 2)
            self.assertEqual(node['review']['findings'][0]['disposition'], 'fixed')
            self.assertEqual(self.engine.load(run)['nodes']['a.repair1']['role'], 'repairer')
        self.for_each_fixture(check)

    def test_looks_good_is_not_a_review(self):
        def check():
            def script(request, call):
                return {'structured': None, 'summary': 'looks good to me'} if request.role == 'reviewer' else {'edits': {'a/x.txt': 'x\n'}, 'structured': {'status': 'done'}}
            synthetic.SCRIPTS['alpha'] = synthetic.SCRIPTS['beta'] = script
            run = self.create(max_stage_retries=1)
            self.assertEqual(self.engine.run_loop(run, max_ticks=30)['state'], 'BLOCKED')
            self.assertFalse(self.engine.load(run)['nodes']['a']['integrated'])
            self.assertEqual(self.engine.load(run)['nodes']['a.review1']['failures'][0]['kind'], 'malformed')
        self.for_each_fixture(check)

    def test_unresolved_findings_after_max_rounds_require_approval(self):
        def check():
            def script(request, call):
                if request.role == 'reviewer': return {'structured': {'status': 'done', 'verdict': 'changes_requested', 'findings': [{'id': '1', 'severity': 'critical', 'summary': 'unsafe'}]}}
                return {'edits': {'a/impl.txt': 'impl\n'}, 'structured': {'status': 'done'}}
            synthetic.SCRIPTS['alpha'] = synthetic.SCRIPTS['beta'] = script
            stopped = self.engine.run_loop(self.create(max_review_rounds=1), max_ticks=30)
            self.assertEqual(stopped['state'], 'APPROVAL_REQUIRED')
            self.assertEqual(stopped['gates'][0]['kind'], 'unresolved_review_findings')
            self.assertFalse(self.engine.load(stopped['run_id'])['nodes']['a']['integrated'])
        self.for_each_fixture(check)

    def test_self_reported_success_cannot_bypass_validators(self):
        def check():
            def script(request, call):
                if request.role == 'reviewer': return {'structured': {'status': 'done', 'verdict': 'approved', 'findings': []}}
                return {'edits': {'a/impl.txt': 'BUG\n'}, 'structured': {'status': 'done', 'summary': 'all tests pass'}}
            synthetic.SCRIPTS['alpha'] = synthetic.SCRIPTS['beta'] = script
            validator = {'kind': 'command', 'command': [sys.executable, '-c', "import pathlib,sys; sys.exit('BUG' in pathlib.Path('a/impl.txt').read_text())"]}
            run = self.engine.create_run('review', repository=self.repo, tasks=[self.task(validators=[validator])], policy={'auto_continue': True, 'max_escalations': 0, 'poll_interval_seconds': 0, 'announce_claims': False})['run_id']
            final = self.engine.run_loop(run, max_ticks=30)
            node = self.engine.load(run)['nodes']['a']
            self.assertEqual(node['result']['self_reported_status'], 'done')
            self.assertFalse(node['validation']['passed'])
            self.assertEqual(final['state'], 'BLOCKED')
        self.for_each_fixture(check)

    def test_integration_refuses_unvalidated_work(self):
        def check():
            run = self.engine.create_run('review', repository=self.repo, tasks=[self.task(validators=[])], policy={'auto_continue': True, 'poll_interval_seconds': 0, 'announce_claims': False})['run_id']
            stopped = self.engine.run_loop(run, max_ticks=30)
            self.assertEqual(stopped['state'], 'APPROVAL_REQUIRED')
            self.assertEqual(stopped['gates'][-1]['kind'], 'policy_restricted_action')
            self.assertFalse(self.engine.load(run)['nodes']['a']['integrated'])
        self.for_each_fixture(check)

    def test_integration_guard_refuses_a_forged_pass(self):
        def check():
            run = self.create(require_independent_review_for_model_edits=False)
            self.engine.start(run); self.engine.step(run)
            record = self.engine.load(run)
            record['nodes']['a'].update(state='PASSED', validation={'passed': False, 'declared_validators': 1, 'evidence': []}, integrated=False)
            self.engine.store.save(record); self.engine.step(run)
            node = self.engine.load(run)['nodes']['a']
            self.assertFalse(node['integrated']); self.assertEqual(node['state'], 'FAILED_FINAL')
            self.assertIn('integration refused', node['wait_reason'])
        self.for_each_fixture(check)

    def test_merge_to_base_requires_approval_then_fast_forwards(self):
        def check():
            run = self.create(final_integration='merge_to_base')
            stopped = self.engine.run_loop(run, max_ticks=40)
            self.assertEqual(stopped['state'], 'APPROVAL_REQUIRED')
            gate = stopped['gates'][-1]
            self.assertEqual(gate['kind'], 'consequential_repository_write')
            before = self.git_repo(self.repo, 'rev-parse', 'main').strip()
            self.assertEqual(before, stopped['base_commit'])
            done = self.engine.decide(run, gate['id'], approve=True)
            self.assertEqual(done['state'], 'COMPLETE')
            self.assertEqual(self.git_repo(self.repo, 'rev-parse', 'main').strip(), done['integration']['head'])
        self.for_each_fixture(check)

    def test_engine_sources_never_invoke_git_push(self):
        root = Path(__file__).resolve().parents[1] / 'src' / 'agent_os' / 'orchestrator'
        for filename in ('engine.py', 'worktrees.py'):
            self.assertNotIn('"push"', (root / filename).read_text(encoding='utf-8'))
