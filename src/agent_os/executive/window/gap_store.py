from __future__ import annotations

import json
from typing import Any

from .brain_dump_store import _utc_seconds
from . import confirm


class GapStore:
    """Persistent knowledge-gap questions and their staged answers."""

    def __init__(self, home=None) -> None:
        self.home = confirm.window_home(home)
        self.path = self.home / 'knowledge-gaps.json'

    def _load(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            data = {}
        if not isinstance(data, dict) or not isinstance(data.get('gaps'), dict):
            return {'gaps': {}}
        return data

    def _save(self, data: dict[str, Any]) -> None:
        confirm._write_json(self.path, data)

    def add(self, gaps, *, tab='personal') -> list[str]:
        data = self._load()
        records = data['gaps']
        added = []
        stored_tab = tab if tab in ('work', 'personal') else 'personal'
        for gap in gaps:
            if not isinstance(gap, dict):
                continue
            gap_id, question = gap.get('id'), gap.get('question')
            if (not isinstance(gap_id, str) or not gap_id.strip()
                    or not isinstance(question, str) or not question.strip()
                    or gap_id in records):
                continue
            records[gap_id] = {
                **gap,
                'tab': stored_tab,
                'status': 'open',
                'added_at': _utc_seconds(),
            }
            added.append(gap_id)
        if added:
            self._save(data)
        return added

    def gaps(self, status='open') -> list[dict]:
        values = list(self._load()['gaps'].values())
        if status is not None:
            values = [gap for gap in values if gap.get('status') == status]
        return sorted(values, key=lambda gap: (gap.get('added_at', ''), gap.get('id', '')))

    def answered_ids(self) -> set[str]:
        return {gap_id for gap_id, gap in self._load()['gaps'].items()
                if gap.get('status') != 'open'}

    def get(self, gap_id: str) -> dict:
        gap = self._load()['gaps'].get(gap_id)
        if gap is None:
            raise KeyError(f'unknown knowledge gap: {gap_id}')
        return gap

    def mark_answered(self, gap_id: str, answer, staging: dict) -> dict:
        data = self._load()
        gap = data['gaps'].get(gap_id)
        if gap is None:
            raise KeyError(f'unknown knowledge gap: {gap_id}')
        gap.update(
            status='answered',
            answer=answer,
            answered_at=_utc_seconds(),
            candidate_ids=[
                item['id'] for key in ('created', 'duplicates')
                for item in staging.get(key, [])
            ],
        )
        self._save(data)
        return gap
