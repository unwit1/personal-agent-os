from __future__ import annotations

import json
import secrets
from typing import Any

from .brain_dump_store import _utc_seconds
from . import confirm

STATUSES = ('drafting', 'awaiting_answers', 'proposed', 'saved', 'discarded')
OPEN_STATUSES = ('drafting', 'awaiting_answers', 'proposed')


class DocumentTaskStore:
    """Persistent document tasks (job descriptions, internal postings) and their questions."""

    def __init__(self, home=None) -> None:
        self.home = confirm.window_home(home)
        self.path = self.home / 'documents' / 'tasks.json'

    def _load(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            data = {}
        if not isinstance(data, dict) or not isinstance(data.get('tasks'), dict):
            return {'tasks': {}}
        return data

    def _save(self, data: dict[str, Any]) -> None:
        confirm._write_json(self.path, data)

    def create(self, doc_type: str, role: str, questions: list[dict], draft: str) -> dict:
        data = self._load()
        doc_id = f'doc-{secrets.token_hex(4)}'
        while doc_id in data['tasks']:
            doc_id = f'doc-{secrets.token_hex(4)}'
        task = {
            'id': doc_id,
            'doc_type': doc_type,
            'role': role,
            'tab': 'work',
            'status': 'awaiting_answers' if any(not q.get('answer') for q in questions) else 'drafting',
            'questions': questions,
            'draft': draft,
            'revisions': [],
            'created_at': _utc_seconds(),
        }
        data['tasks'][doc_id] = task
        self._save(data)
        return task

    def get(self, doc_id: str) -> dict:
        task = self._load()['tasks'].get(doc_id)
        if task is None:
            raise KeyError(f'unknown document task: {doc_id}')
        return task

    def tasks(self, statuses=OPEN_STATUSES) -> list[dict]:
        values = list(self._load()['tasks'].values())
        if statuses is not None:
            values = [task for task in values if task.get('status') in statuses]
        return sorted(values, key=lambda task: (task.get('created_at', ''), task.get('id', '')))

    def update(self, doc_id: str, **fields) -> dict:
        if 'status' in fields and fields['status'] not in STATUSES:
            raise ValueError(f"unknown status: {fields['status']}")
        data = self._load()
        task = data['tasks'].get(doc_id)
        if task is None:
            raise KeyError(f'unknown document task: {doc_id}')
        task.update(fields, updated_at=_utc_seconds())
        self._save(data)
        return task

    def add_revision(self, doc_id: str, revision: dict) -> dict:
        data = self._load()
        task = data['tasks'].get(doc_id)
        if task is None:
            raise KeyError(f'unknown document task: {doc_id}')
        task.setdefault('revisions', []).append(revision)
        task.update(status='saved', updated_at=_utc_seconds())
        self._save(data)
        return task
