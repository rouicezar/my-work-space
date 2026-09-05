"""Production submission must survive client loss without inventing runtime state."""

import json
import tempfile
import unittest
import uuid
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

from forma_ai.herdr_adapter import HerdrTask, HerdrWorkspace
from forma_ai.system_resources import MemoryEvidence
from forma_ai.task_metadata_store import TaskMetadataStore
from scripts import supervisor
from tests import test_supervisor as supervisor_helpers
from tests import test_herdr_integration as live_helpers


class SubmissionHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'Product'
        helpers = supervisor_helpers.SupervisorProtocolTests()
        self.task_id = str(uuid.uuid4())
        self.args = helpers.task_submit_args(
            self.root, helpers.write_current_cloud_catalog(Path(self.temp.name)), self.task_id,
        )
        self.body = helpers.task_submit_body(prompt='整理项目资料')
        self.adapter = Mock()
        self.adapter.open_workspace.return_value = HerdrWorkspace('w1', 'w1:p1')
        self.started = HerdrTask(self.task_id, f'herdr:{self.task_id}:w1:p1',
                                 'w1', 'w1:p1', 'term1', 'idle', 1)
        self.adapter.spawn_task.return_value = self.started
        self.adapter.prompt_task.return_value = replace(self.started, state='running', revision=2)
        for target, value in (
            ('_herdr_adapter_for_root', self.adapter),
            ('_qwen_agent_environment', {}),
            ('_runtime_secrets', ('a', 'b', 'c')),
            ('measure_available_memory', MemoryEvidence(8192, True, 'AVAILABLE_MEMORY_MEASURED')),
        ):
            patcher = patch.object(supervisor, target, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(supervisor.RuntimeManager, 'status',
                               return_value={'phase': 'running', 'herdr_alive': True})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_normal_submit_persists_intent_before_launch_and_ack_before_prompt(self):
        def open_workspace(**kwargs):
            record = TaskMetadataStore(self.root).load(self.task_id)
            self.assertEqual(record.intent_label, '整理项目资料')
            self.assertIsNone(record.run_id)
            return HerdrWorkspace('w1', 'w1:p1')

        def prompt(**kwargs):
            record = TaskMetadataStore(self.root).load(self.task_id)
            self.assertEqual(record.herdr_terminal_id, 'term1')
            self.assertEqual(record.last_accepted_revision, 1)
            return replace(self.started, state='running', revision=2)

        self.adapter.open_workspace.side_effect = open_workspace
        self.adapter.prompt_task.side_effect = prompt
        response = supervisor.run(self.args, input_data=self.body)
        self.assertEqual(response['payload']['result']['finish_reason'], 'accepted')
        record = TaskMetadataStore(self.root).load(self.task_id)
        self.assertEqual(record.last_accepted_revision, 2)
        self.assertEqual(record.run_id, self.started.run_id)
        raw = json.loads((self.root / 'state/task-metadata' / f'{self.task_id}.json').read_text())
        self.assertNotIn('runtime_state', raw)

    def test_prompt_failure_retains_acknowledged_run_for_recovery(self):
        self.adapter.prompt_task.side_effect = TimeoutError('client lost prompt acknowledgement')
        response = supervisor.run(self.args, input_data=self.body)
        self.assertEqual(response['status'], 'error')
        self.assertIn('History', response['error']['message'])
        record = TaskMetadataStore(self.root).load(self.task_id)
        self.assertEqual(record.run_id, self.started.run_id)
        self.assertEqual(record.last_accepted_revision, 1)

    def test_duplicate_submit_does_not_launch_another_agent(self):
        supervisor.run(self.args, input_data=self.body)
        supervisor.run(self.args, input_data=self.body)
        self.assertEqual(self.adapter.open_workspace.call_count, 1)

    def test_store_failure_prevents_agent_launch(self):
        with patch.object(TaskMetadataStore, 'save', side_effect=OSError('disk full')):
            supervisor.run(self.args, input_data=self.body)
        self.adapter.open_workspace.assert_not_called()

    def test_reopen_reconciles_new_revision_but_rejects_reused_pane_identity(self):
        from forma_ai.task_metadata_reconcile import build_reconcile_payload
        from tests.test_task_history_recovery import sample_snapshot
        supervisor.run(self.args, input_data=self.body)
        snapshot = sample_snapshot(pane_id='w1:p1', workspace_id='w1', terminal_id='term1',
                                   revision=7, agent_status='working')
        source = Mock(snapshot=Mock(return_value=snapshot))
        result = build_reconcile_payload(self.root, runtime_status=lambda: {'herdr_alive': True},
                                         snapshot_source=source)
        self.assertEqual(result['tasks'][0]['last_accepted_revision'], 7)
        self.assertEqual(TaskMetadataStore(self.root).load(self.task_id).last_accepted_revision, 7)
        source.snapshot.return_value = replace(snapshot, agents=(
            replace(snapshot.agents[0], terminal_id='replacement-terminal', agent_status='done'),
        ))
        result = build_reconcile_payload(self.root, runtime_status=lambda: {'herdr_alive': True},
                                         snapshot_source=source)
        self.assertEqual(result['tasks'][0]['display_outcome'], 'unknown')
        self.assertTrue(result['tasks'][0]['reconciliation_required'])

    def test_restart_without_herdr_keeps_intent_visible_as_unknown(self):
        from forma_ai.task_metadata_reconcile import build_reconcile_payload
        supervisor.run(self.args, input_data=self.body)
        result = build_reconcile_payload(self.root, runtime_status=lambda: {'herdr_alive': False})
        self.assertEqual(result['tasks'][0]['intent_label'], '整理项目资料')
        self.assertEqual(result['tasks'][0]['display_outcome'], 'unknown')
        self.assertFalse(result['tasks'][0]['may_resume'])

    def test_reopened_normal_task_reclaims_and_cancel_requires_latest_revision(self):
        from forma_ai.herdr_adapter import HerdrLifecycleResult
        from tests.test_task_history_recovery import sample_snapshot
        supervisor.run(self.args, input_data=self.body)
        self.adapter.snapshot.return_value = sample_snapshot(
            pane_id='w1:p1', workspace_id='w1', terminal_id='term1', revision=7,
            agent_status='blocked')
        self.adapter.reclaim_task.return_value = replace(self.started, revision=7, state='blocked')
        self.adapter.cancel_task.return_value = HerdrLifecycleResult(
            self.task_id, self.started.run_id, 'graceful_interrupt', 'cancel_requested', 7)
        def command(name, *extra):
            return supervisor.run(supervisor.parser().parse_args([
                '--request-id', str(uuid.uuid4()), name, '--root', str(self.root),
                '--task-id', self.task_id, *extra]))
        self.assertEqual(command('task-history-reclaim')['payload']['revision'], 7)
        rejected = command('task-history-cancel', '--expected-revision', '2')
        self.assertEqual(rejected['error']['code'], 'RECOVERY_REVISION_MISMATCH')
        self.adapter.cancel_task.assert_not_called()
        accepted = command('task-history-cancel', '--expected-revision', '7')
        self.assertEqual(accepted['payload']['state'], 'cancel_requested')
        self.assertEqual(self.adapter.cancel_task.call_args.kwargs['expected_revision'], 7)

    def test_fresh_run_rejects_world_readable_saved_intent(self):
        supervisor.run(self.args, input_data=self.body)
        (self.root / 'state/task-intents' / f'{self.task_id}.json').chmod(0o644)
        args = supervisor.parser().parse_args([
            '--request-id', str(uuid.uuid4()), 'task-history-fresh-run', '--root', str(self.root),
            '--task-id', self.task_id])
        response = supervisor.run(args)
        self.assertEqual(response['error']['code'], 'RECOVERY_INTENT_UNAVAILABLE')
        self.assertEqual(self.adapter.open_workspace.call_count, 1)

    def test_fresh_run_replays_saved_intent_into_new_task_without_overwriting_history(self):
        supervisor.run(self.args, input_data=self.body)
        original = TaskMetadataStore(self.root).load(self.task_id)
        new_id = str(uuid.uuid4())
        fresh = replace(self.started, task_id=new_id, run_id=f'herdr:{new_id}:w2:p1',
                        workspace_id='w2', pane_id='w2:p1', terminal_id='term2')
        self.adapter.open_workspace.return_value = HerdrWorkspace('w2', 'w2:p1')
        self.adapter.spawn_task.return_value = fresh
        self.adapter.prompt_task.return_value = replace(fresh, revision=2, state='running')
        args = supervisor.parser().parse_args([
            '--request-id', new_id, 'task-history-fresh-run', '--root', str(self.root),
            '--task-id', self.task_id,
        ])
        result = supervisor.run(args)
        self.assertEqual(result['payload']['task_id'], new_id)
        self.assertEqual(result['payload']['previous_task_id'], self.task_id)
        self.assertEqual(TaskMetadataStore(self.root).load(self.task_id), original)
        self.assertEqual(TaskMetadataStore(self.root).load(new_id).herdr_terminal_id, 'term2')
        self.assertEqual(self.adapter.prompt_task.call_args.kwargs['text'], '整理项目资料')


@unittest.skipUnless(live_helpers._find_herdr_binary(), 'verified Herdr binary unavailable')
class NormalSubmissionLiveHerdrTests(live_helpers.HerdrFixtureAgentIntegrationTestCase):
    """Real Herdr/normal Supervisor path; deterministic provider-free fixture, not Qwen acceptance."""
    PROOF_ID = 'C1-T04'

    def test_normal_submission_survives_client_restart_and_recovery(self):
        from forma_ai.herdr_adapter import HerdrAdapter
        from forma_ai.herdr_transport import HerdrSocketTransport

        root = Path(self.temp_root.name) / 'Product'
        fixture_home = Path(self.temp_root.name) / 'fixture-home'
        fixture_home.mkdir()
        fixture_path = f'{self.fixture_bin}:/usr/bin:/bin'
        (fixture_home / '.bash_profile').write_text(f'export PATH={fixture_path!r}\n')
        environment = {'HOME': str(fixture_home), 'PATH': fixture_path}
        helper = supervisor_helpers.SupervisorProtocolTests()
        task_id = str(uuid.uuid4())
        args = helper.task_submit_args(root, helper.write_current_cloud_catalog(Path(self.temp_root.name)), task_id)
        original_spawn = self.adapter.spawn_task
        original_dispatch = supervisor._dispatch_local_agent_task

        def checked_dispatch(**kwargs):
            try:
                return original_dispatch(**kwargs)
            except supervisor.LocalTaskError as exc:
                self.fail(f'fixture dispatch failed: {exc!r}; cause={exc.__cause__!r}')

        def spawn_fixture(**kwargs):
            # Only the provider boundary is replaced. No real Codex/cloud credentials are used.
            self.assertEqual(kwargs['agent_kind'], 'qwen')
            kwargs['agent_kind'] = 'codex'
            kwargs['startup_timeout_ms'] = 5000
            return original_spawn(**kwargs)

        with patch.object(supervisor, '_herdr_adapter_for_root', side_effect=lambda _: self.adapter), \
             patch.object(supervisor, '_herdr_socket_path', return_value=self.socket_path), \
             patch.object(supervisor, '_dispatch_local_agent_task', side_effect=checked_dispatch), \
             patch.object(supervisor, '_qwen_agent_environment', return_value=environment), \
             patch.object(supervisor, '_runtime_secrets', return_value=('a', 'b', 'c')), \
             patch.object(supervisor, 'measure_available_memory', return_value=MemoryEvidence(8192, True, 'AVAILABLE_MEMORY_MEASURED')), \
             patch.object(supervisor.RuntimeManager, 'status', return_value={'phase': 'running', 'herdr_alive': True}), \
             patch.object(self.adapter, 'spawn_task', side_effect=spawn_fixture):
            self._stage('normal task-submit with deterministic provider fixture')
            response = supervisor.run(args, input_data=helper.task_submit_body(prompt='fixture-blocked'))
            self.assertEqual(response['status'], 'ok', response)
            record = TaskMetadataStore(root).load(task_id)
            self.transport('agent.wait', {'target': record.herdr_pane_id,
                                         'until': ['blocked'], 'timeout_ms': 5000})
            self._stage('discard client and rebuild adapter from persisted intent')
            self.transport = HerdrSocketTransport(socket_path=self.socket_path, environ={}, request_timeout=15)
            self.adapter = HerdrAdapter(executable_finder=lambda _: self.binary,
                request=self.transport, probe=self.transport.probe)

            def command(name, *extra):
                return supervisor.run(supervisor.parser().parse_args([
                    '--request-id', str(uuid.uuid4()), name, '--root', str(root),
                    '--task-id', task_id, *extra]))

            reconciled = command('task-metadata-reconcile')['payload']['tasks'][0]
            self.assertEqual(reconciled['runtime_state'], 'blocked')
            reclaimed = command('task-history-reclaim')
            self.assertEqual(reclaimed['payload']['run_id'], record.run_id)
            self._stage('cancel recovered task against authoritative revision')
            cancelled = command('task-history-cancel', '--expected-revision',
                                str(reconciled['last_accepted_revision']))
            self.assertEqual(cancelled['payload']['state'], 'cancel_requested')
            self.assertEqual(command('task-metadata-reconcile')['payload']['tasks'][0]['runtime_state'], 'blocked')
            self._stage('noncooperative interrupt is not falsely marked cancelled')
            original_spawn = self.adapter.spawn_task
            before_fresh = TaskMetadataStore(root).load(task_id)
            with patch.object(self.adapter, 'spawn_task', side_effect=spawn_fixture):
                fresh = command('task-history-fresh-run')
            self.assertEqual(fresh['status'], 'ok', fresh)
            fresh_id = fresh['payload']['task_id']
            self.assertNotEqual(fresh_id, task_id)
            self.assertNotEqual(fresh['payload']['pane_id'], record.herdr_pane_id)
            self.assertEqual(TaskMetadataStore(root).load(task_id), before_fresh)
            self.assertEqual(TaskMetadataStore(root).load(fresh_id).intent_label, 'fixture-blocked')
            self._stage('fresh run creates its own persisted task and preserves previous history')
