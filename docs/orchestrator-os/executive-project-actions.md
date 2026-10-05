# EXEC-1 Per-Project Next Action Engine

The per-project Next Action Engine synthesizes next action metadata from project state, ranking and scanning projects by goal, priorities, blockers, and decisional status.

## Project State Fields

Project state (typically from `projects/*/state.json`) contains these optional fields:

- **goal**: Long-term objective for the project. Falls back to `summary` if empty or missing.
- **current_state**: Current progress or phase (e.g., "In design review", "Waiting on feedback").
- **next_action**: The immediate concrete action to take next (e.g., "Review PR #123", "Deploy to staging").
- **current_priorities**: List of priority items in order. The first non-empty entry becomes `next_action` if `next_action` is not set.
- **blockers**: List of blocking issues preventing progress (e.g., "Waiting for API review").
- **waiting_on**: List of external dependencies (e.g., "Design approval", "Budget sign-off").
- **decisions_needed**: List of decisions the project owner/user must make. Requires user involvement.
- **delegable_work**: List of work agents can execute without user input (e.g., "Write unit tests", "Update documentation").
- **updated_at**: ISO 8601 timestamp of last state update. Used to calculate age and detect staleness.

## Next Action Synthesis

`project_next_action(state, *, today, stale_days=30)` extracts and synthesizes action metadata from a single project state:

- **goal** is extracted from the `goal` field. If empty or missing, falls back to `summary`.
- **current_state** is extracted as a single string. Whitespace-only values are treated as None.
- **next_action** is extracted from the `next_action` field. If not present or empty, the function uses the first non-empty entry from `current_priorities`.
- **next_action_source** indicates where `next_action` came from: `"next_action"`, `"current_priorities"`, or None if neither is available.
- List fields (**blockers**, **waiting_on**, **decisions_needed**, **delegable_work**) are filtered to remove non-strings and whitespace-only entries.
- **age_days** is calculated from `updated_at` as the number of days since that date (relative to `today`). Non-parseable dates result in None.

### Fallback Rules

- **Goal:** Uses `goal` field; falls back to `summary` if goal is empty, missing, non-string, or whitespace-only.
- **Next Action:** Uses `next_action` field if non-empty; falls back to the first non-empty entry in `current_priorities`.

## Status Flags

Flags are generated based on the extracted state and are always sorted alphabetically:

- **no_next_action**: Set if `next_action` is None (neither `next_action` nor `current_priorities` yielded a concrete action).
- **stalled**: Set if `age_days` exceeds the `stale_days` threshold (default 30 days). Indicates a project has not been updated in a long time.
- **unknown_age**: Set if `age_days` is None (missing or unparseable `updated_at` date).
- **blocked**: Set if either `blockers` or `waiting_on` is non-empty. Indicates active blockers or dependencies.
- **needs_decision**: Set if `decisions_needed` is non-empty. Indicates decisions awaiting the project owner/user.

## Decisions vs. Delegable Work

- **decisions_needed**: Items requiring user decision-making. The project is waiting on the user to make a choice (e.g., "Should we rewrite the API?" or "Which platform should we target?").
- **delegable_work**: Work agents can execute autonomously without user involvement (e.g., "Write unit tests", "Refactor logging").

A project with items in `delegable_work` but no `decisions_needed` is unblocked for agent execution. A project with `decisions_needed` is waiting for user input.

## Scanning Projects

`scan(states, *, today, stale_days=30, include_inactive=False)` scans a list of project states and returns aggregated results:

- **include_inactive**: If False (default), only projects with `status == "active"` are scanned. If True, all projects are included.
- **projects**: List of results from `project_next_action` for each scanned project, sorted by project id.
- **stalled**: List of project ids with the `stalled` flag set.
- **no_next_action**: List of project ids with the `no_next_action` flag set.
- **needs_decision**: List of project ids with the `needs_decision` flag set.
- **stale_days**: The threshold used for staleness detection.

The scan result allows quick identification of projects in specific conditions (e.g., all stalled projects, all projects awaiting decisions).

## Default Constant

**STALE_DAYS_DEFAULT**: 30 days. Projects not updated within this period are flagged as stalled.

## CLI Commands

### `agent-os executive project-next <project>`

Get the next action and full synthesized metadata for a specific project.

Arguments:
- `<project>`: Project identifier (e.g., `personal-agent-os`).

Options:
- `--stale-days N`: Threshold for staleness detection (default: 30). Overrides the default.
- `--today YYYY-MM-DD`: Reference date for age calculation (default: today). Useful for testing or replaying analysis.

Output: JSON dict with goal, current_state, next_action, next_action_source, blockers, waiting_on, decisions_needed, delegable_work, updated_at, age_days, and flags.

### `agent-os executive project-scan [--all]`

Scan all active projects (or all projects with `--all`) and return aggregated status flags and rankings.

Options:
- `--all`: Include inactive projects (status != "active"). Without this, only active projects are scanned.
- `--stale-days N`: Threshold for staleness detection (default: 30).
- `--today YYYY-MM-DD`: Reference date for age calculation (default: today).

Output: JSON dict with:
- `projects`: Sorted list of all scanned projects with their next action metadata.
- `stalled`: Project ids flagged as stalled.
- `no_next_action`: Project ids with no next action.
- `needs_decision`: Project ids awaiting user decisions.
- `stale_days`: The threshold used.

## MCP Tools

The per-project Next Action Engine is exposed to Claude models through read-only MCP tools.

### `executive_projects.next`

**Description:** Get the next action and full synthesized metadata for a specific project.

**Input schema:**
```json
{
  "project": "string (required) — project identifier",
  "stale_days": "integer (optional) — staleness threshold (default 30)",
  "today": "string (optional) — reference date YYYY-MM-DD (default today)"
}
```

**Output:** JSON dict with goal, current_state, next_action, next_action_source, blockers, waiting_on, decisions_needed, delegable_work, updated_at, age_days, and flags. Local-only, never leaves the machine.

### `executive_projects.scan`

**Description:** Scan all active or all projects and return aggregated status with per-category project lists.

**Input schema:**
```json
{
  "include_all": "boolean (optional) — include inactive projects (default false)",
  "stale_days": "integer (optional) — staleness threshold (default 30)",
  "today": "string (optional) — reference date YYYY-MM-DD (default today)"
}
```

**Output:** JSON dict with:
- `projects`: Sorted list of all scanned projects with their next action metadata.
- `stalled`: Project ids flagged as stalled.
- `no_next_action`: Project ids with no next action.
- `needs_decision`: Project ids awaiting user decisions.
- `stale_days`: The threshold used.

Local-only, never leaves the machine.

## Open

Not yet implemented:

- **Repeated-deferral detection**: Tracking and alerting when a project is repeatedly deferred without progress (no update for multiple scan cycles).
- **Vague work to concrete action**: Heuristics to convert high-level goals or vague work items into concrete, measurable next actions.
