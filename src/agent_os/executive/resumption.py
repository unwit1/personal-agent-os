"""Build compact, pure project resumption packets from project state."""

from __future__ import annotations

from datetime import date

from agent_os.executive import project_actions

PACKET_SCHEMA = 'agent-os/resumption-packet@1'


def resumption_packet(
    state: dict,
    *,
    today: date,
    stale_days: int = project_actions.STALE_DAYS_DEFAULT,
    max_items: int = 3,
    max_chars: int = 280,
) -> dict:
    """Return a compact summary of project state and its next action."""
    result = project_actions.project_next_action(state, today=today, stale_days=stale_days)
    truncated = False

    def compact(value):
        nonlocal truncated
        if isinstance(value, str) and len(value) > max_chars:
            truncated = True
            return value[: max_chars - 1] + '…'
        return value

    loops = {}
    for key, source in (
        ('blockers', 'blockers'),
        ('waiting_on', 'waiting_on'),
        ('decisions_needed', 'decisions_needed'),
    ):
        items = result[source]
        if len(items) > max_items:
            truncated = True
        loops[key] = [compact(item) for item in items[:max_items]]

    suggested = 'vague_next_action' in result['flags'] and result['suggested_next_action']
    next_action = result['suggested_next_action'] if suggested else result['next_action']
    return {
        'schema': PACKET_SCHEMA,
        'project': result['project'],
        'status': result['status'],
        'goal': compact(result['goal']),
        'where_you_left_off': compact(result['current_state']),
        'next_action': compact(next_action),
        'next_action_source': 'suggested' if suggested else result['next_action_source'],
        'open_loops': loops,
        'age_days': result['age_days'],
        'flags': result['flags'],
        'truncated': truncated,
    }
