"""Open document tasks and their unanswered questions as Executive window items."""

from __future__ import annotations

from .. import documents
from .doc_store import DocumentTaskStore


def _waiting_on(task: dict) -> str:
    status = task.get('status')
    unanswered = len(documents.open_questions(task.get('questions') or []))
    if status == 'proposed':
        return 'Proposed; waiting on your Confirm to save'
    if unanswered:
        return f'Waiting on your answers to {unanswered} question(s)'
    return 'Draft ready; waiting on you to propose it for saving'


def document_items(store=None) -> list[dict]:
    """Return one document_task per open task and one document_question per unanswered question.

    Tasks for the same role that share an unanswered question (a job description and an
    internal posting) get that question once; the answer is applied to every task."""
    if store is None:
        store = DocumentTaskStore()
    items = []
    tasks = store.tasks()
    shared: dict[tuple[str, str], list[str]] = {}
    for task in tasks:
        for question in documents.open_questions(task.get('questions') or []):
            shared.setdefault((task['role'].strip().lower(), question['id']), []).append(task['id'])
    for task in tasks:
        label = documents.DOC_LABELS.get(task['doc_type'], task['doc_type'])
        items.append({
            'id': f"document:{task['id']}",
            'kind': 'document_task',
            'title': f"{label}: {task['role']}",
            'tab': task.get('tab', 'work'),
            'source': 'Documents',
            'sensitivity': 'work',
            'why': _waiting_on(task),
            'context': {'doc_id': task['id'], 'doc_type': task['doc_type'],
                        'role': task['role'], 'status': task.get('status')},
        })
        for question in documents.open_questions(task.get('questions') or []):
            doc_ids = shared[(task['role'].strip().lower(), question['id'])]
            if doc_ids[0] != task['id']:
                continue  # asked once, on the first task that needs it
            context = {'doc_id': task['id'], 'question_id': question['id']}
            if len(doc_ids) > 1:
                context['doc_ids'] = list(doc_ids)
                why = f"Needed before the drafts for {task['role']} can be saved"
            else:
                why = f"Needed before the {label.lower()} for {task['role']} can be saved"
            items.append({
                'id': f"document-question:{task['id']}:{question['id']}",
                'kind': 'document_question',
                'title': question['text'],
                'tab': task.get('tab', 'work'),
                'source': 'Documents',
                'sensitivity': 'work',
                'why': why,
                'context': context,
            })
    return items
