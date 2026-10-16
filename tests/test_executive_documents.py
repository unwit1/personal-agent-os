import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import json

import pytest

from agent_os.executive import documents
from agent_os.executive.window import actions_documents, confirm, doc_store, providers_documents, registry


@pytest.fixture
def env(tmp_path, monkeypatch):
    home = tmp_path / 'window'
    out = tmp_path / 'out'
    monkeypatch.setenv(confirm.ENV_HOME, str(home))
    monkeypatch.setattr(actions_documents, 'OUTPUT_BASE', out)
    monkeypatch.setattr(
        documents.local_paths, 'is_gitignored_local_path',
        lambda path, **_: out.resolve() in Path(path).resolve().parents,
    )
    reg = registry.Registry()
    actions_documents.register(reg)
    return reg, confirm.PendingStore(home), out


def _task_item(doc_id):
    return {'id': f'document:{doc_id}', 'kind': 'document_task', 'context': {'doc_id': doc_id}}


def _start(reg, pending, doc_type='internal_posting'):
    started = reg.invoke('document.start', {'id': 'document-start', 'kind': 'document_start'},
                         {'doc_type': doc_type, 'role': 'Executive Assistant'}, pending)
    assert started['status'] == 'done'
    return started['result']


def test_shared_questions_asked_once_and_applied_to_both_tasks(env):
    reg, pending, _out = env
    job = _start(reg, pending, 'job_description')
    posting = _start(reg, pending, 'internal_posting')

    items = providers_documents.document_items()
    questions = [i for i in items if i['kind'] == 'document_question']
    titles = [i['title'] for i in questions]
    assert len(titles) == len(set(titles))
    assert len(questions) == len(posting['questions'])  # the posting asks a superset
    shared = next(i for i in questions if i['context']['question_id'] == 'reports_to')
    assert set(shared['context']['doc_ids']) == {job['doc_id'], posting['doc_id']}
    only_posting = next(i for i in questions if i['context']['question_id'] == 'how_to_apply')
    assert 'doc_ids' not in only_posting['context']

    reg.invoke('document.answer', shared, {'answer': 'The Director'}, pending)
    store = doc_store.DocumentTaskStore()
    for doc_id in (job['doc_id'], posting['doc_id']):
        answers = {q['id']: q['answer'] for q in store.get(doc_id)['questions']}
        assert answers['reports_to'] == 'The Director'
    remaining = [i['context']['question_id'] for i in providers_documents.document_items()
                 if i['kind'] == 'document_question']
    assert 'reports_to' not in remaining


def test_full_flow_start_answer_propose_save(env):
    reg, pending, out = env
    started = _start(reg, pending)
    doc_id = started['doc_id']
    assert started['status'] == 'awaiting_answers'
    assert '## Class Title' in started['draft'] and '## Who May Apply' in started['draft']
    qids = {q['id'] for q in started['questions']}
    assert {'reports_to', 'flsa', 'pay', 'schedule', 'duties', 'qualifications',
            'posting_window', 'how_to_apply'} == qids

    items = providers_documents.document_items()
    kinds = [i['kind'] for i in items]
    assert kinds.count('document_task') == 1 and kinds.count('document_question') == len(qids)
    assert 'Waiting on your answers' in items[0]['why']

    answers = {qid: f'answer {qid}' for qid in qids - {'how_to_apply'}}
    answered = reg.invoke('document.answer', _task_item(doc_id), {'answers': answers}, pending)['result']
    assert answered['open_questions'] == [{'id': 'how_to_apply', 'text': 'How should current employees apply?'}]
    question_item = {'id': 'q', 'kind': 'document_question',
                     'context': {'doc_id': doc_id, 'question_id': 'how_to_apply'}}
    answered = reg.invoke('document.answer', question_item, {'answer': 'Email HR', 'changes': 'Add board minutes'},
                          pending)['result']
    assert answered['status'] == 'drafting' and answered['open_questions'] == []
    assert 'Email HR' in answered['draft'] and 'Add board minutes' in answered['draft']

    proposed = reg.invoke('document.propose', _task_item(doc_id), {}, pending)
    assert proposed['status'] == 'needs_confirmation'
    assert proposed['preview']['content'].startswith('--- saved')
    assert proposed['preview']['open_questions'] == []
    reg.confirm(proposed['confirm_token'], pending)
    assert doc_store.DocumentTaskStore().get(doc_id)['status'] == 'proposed'
    with pytest.raises(KeyError):
        reg.confirm(proposed['confirm_token'], pending)

    final_text = answered['draft'] + '\nFinal edit.\n'
    saved_preview = reg.invoke('document.save', _task_item(doc_id), {'text': final_text}, pending)
    assert saved_preview['status'] == 'needs_confirmation'
    preview = saved_preview['preview']
    assert preview['content'] == final_text
    md_target = out / 'executive-assistant' / 'internal_posting-v1.md'
    assert preview['paths'][0] == str(md_target)
    assert not out.exists()  # nothing written before Confirm

    result = reg.confirm(saved_preview['confirm_token'], pending)
    assert set(result) == {'doc_id', 'path', 'sha256'}
    assert md_target.read_text(encoding='utf-8') == final_text
    assert result['sha256'] == documents.sha256(final_text) == preview['sha256']
    if documents.docx_available():
        assert md_target.with_suffix('.docx').exists()
    with pytest.raises(KeyError):
        reg.confirm(saved_preview['confirm_token'], pending)

    task = doc_store.DocumentTaskStore().get(doc_id)
    assert task['status'] == 'saved'
    assert task['revisions'] == [{'n': 1, 'sha256': result['sha256'], 'path': str(md_target)}]
    assert providers_documents.document_items() == []
    audit_text = pending.audit_path.read_text()
    audit = [json.loads(line) for line in audit_text.splitlines()]
    assert audit[-1]['result'] == result
    assert audit[-1]['params']['text_sha256'] == result['sha256']
    assert 'Final edit.' not in audit_text and 'Email HR' not in audit_text


def test_second_task_for_same_role_saves_next_version(env):
    reg, pending, out = env
    first = _start(reg, pending, 'job_description')['doc_id']
    saved = reg.invoke('document.save', _task_item(first), {'text': 'first\n'}, pending)
    reg.confirm(saved['confirm_token'], pending)
    second = _start(reg, pending, 'job_description')['doc_id']
    preview = reg.invoke('document.save', _task_item(second), {'text': 'second\n'}, pending)
    assert preview['preview']['paths'][0].endswith('job_description-v2.md')
    result = reg.confirm(preview['confirm_token'], pending)
    assert Path(result['path']).read_text(encoding='utf-8') == 'second\n'
    assert (out / 'executive-assistant' / 'job_description-v1.md').read_text(encoding='utf-8') == 'first\n'


def test_stale_propose_refuses_and_keeps_newer_draft(env):
    reg, pending, out = env
    doc_id = _start(reg, pending, 'job_description')['doc_id']
    proposed = reg.invoke('document.propose', _task_item(doc_id), {}, pending)
    reg.invoke('document.answer', _task_item(doc_id), {'changes': 'Add travel'}, pending)
    newer = doc_store.DocumentTaskStore().get(doc_id)['draft']
    with pytest.raises(ValueError, match='draft changed since preview'):
        reg.confirm(proposed['confirm_token'], pending)
    task = doc_store.DocumentTaskStore().get(doc_id)
    assert task['draft'] == newer and task.get('draft_source', 'template') == 'template'

    reg.invoke('document.answer', _task_item(doc_id), {'text': '# Hand-written\n'}, pending)
    answered = reg.invoke('document.answer', _task_item(doc_id), {'answers': {'pay': 'Grade 12'}}, pending)
    assert answered['result']['draft'] == '# Hand-written\n'
    assert 'unchanged' in answered['result']['note']


def test_save_writes_pinned_preview_text_not_current_draft(env):
    reg, pending, out = env
    doc_id = _start(reg, pending, 'job_description')['doc_id']
    preview = reg.invoke('document.save', _task_item(doc_id), {}, pending)
    previewed = preview['preview']['content']
    reg.invoke('document.answer', _task_item(doc_id), {'text': '# Changed after preview\n'}, pending)
    result = reg.confirm(preview['confirm_token'], pending)
    assert Path(result['path']).read_text(encoding='utf-8') == previewed


def test_propose_diffs_against_last_saved_version(env):
    reg, pending, out = env
    doc_id = _start(reg, pending, 'job_description')['doc_id']
    saved = reg.invoke('document.save', _task_item(doc_id), {'text': 'line one\n'}, pending)
    reg.confirm(saved['confirm_token'], pending)
    reg.invoke('document.answer', _task_item(doc_id), {'text': 'line one\nline two\n'}, pending)
    proposed = reg.invoke('document.propose', _task_item(doc_id), {}, pending)['preview']
    assert '+line two' in proposed['content'] and '-line one' not in proposed['content']
    second = reg.invoke('document.save', _task_item(doc_id), {}, pending)
    assert second['preview']['paths'][0].endswith('job_description-v2.md')


def test_refuses_when_output_path_not_gitignored(env, monkeypatch):
    reg, pending, out = env
    doc_id = _start(reg, pending, 'job_description')['doc_id']
    preview = reg.invoke('document.save', _task_item(doc_id), {}, pending)
    monkeypatch.setattr(documents.local_paths, 'is_gitignored_local_path', lambda path, **_: False)
    with pytest.raises(ValueError, match='gitignored'):
        reg.confirm(preview['confirm_token'], pending)
    with pytest.raises(ValueError, match='gitignored'):
        reg.invoke('document.save', _task_item(doc_id), {}, pending)
    assert not out.exists()


def test_discard_and_bad_params(env):
    reg, pending, out = env
    with pytest.raises(ValueError):
        reg.invoke('document.start', {}, {'doc_type': 'memo', 'role': 'X'}, pending)
    doc_id = _start(reg, pending)['doc_id']
    with pytest.raises(ValueError, match='unknown question'):
        reg.invoke('document.answer', _task_item(doc_id), {'answers': {'nope': 'x'}}, pending)
    reg.invoke('document.discard', _task_item(doc_id), {}, pending)
    assert providers_documents.document_items() == []
    with pytest.raises(ValueError, match='discarded'):
        reg.invoke('document.save', _task_item(doc_id), {}, pending)
