# EXEC-1 Per-Project Next Action Engine

The per-project Next Action Engine (`src/agent_os/executive/project_actions.py`) derives next-action metadata and status flags from each project's state, and scans all registered projects to list those that are stalled, blocked, waiting on a decision, or missing a concrete next action.

## Project State Fields

Project state (typically from `projects/*/state.json`) contains these optional fields:

- **goal**: Long-term objective for the project. Falls back to `summary` if empty or missing.
- **current_state**: Current progress or phase (e.g., "In design review", "Waiting on feedback").
- **next_action**: The immediate concrete action to take next (e.g., "Review PR #123", "Deploy to staging").
- **current_priorities**: List of priority items in order. The first non-empty entry becomes `next_action` if `next_action` is not set.
- **blockers**: List of blocking issues preventing progress (e.g., "Waiting for API review").
- **waiting_on**: List of external dependencies (e.g., "Design approval", "Budget sign-off").
- **decisions_needed**: List of decisions the project owner/user must make. Requires user involvement.
- **decisions_resolved**: Optional list of resolved decisions, each recorded with its decision text, resolution, and resolution date.
- **delegable_work**: List of work agents can execute without user input (e.g., "Write unit tests", "Update documentation").
- **updated_at**: ISO 8601 timestamp of last state update. Used to calculate age and detect staleness.

The project's snooze count (`deferrals`) is not a state field: callers pass it in, derived from Event Bus events (see Repeated Deferrals).

## Next Action Synthesis

`project_next_action(state, *, today, stale_days=30)` extracts and synthesizes action metadata from a single project state:

- **goal** is extracted from the `goal` field. If empty or missing, falls back to `summary`.
- **current_state** is extracted as a single string. Whitespace-only values are treated as None.
- **next_action** is extracted from the `next_action` field. If not present or empty, the function uses the first non-empty entry from `current_priorities`.
- **next_action_source** indicates where `next_action` came from: `"next_action"`, `"current_priorities"`, or None if neither is available.
- **suggested_next_action**: see Suggested Next Action below.
- List fields (**blockers**, **waiting_on**, **decisions_needed**, **delegable_work**) are normalized in the synthesized result: whitespace is trimmed; invalid (non-string) and blank entries are ignored; duplicate entries are removed case-sensitively; and the first-occurrence order is preserved. This is a read-time normalization only and does not rewrite `state.json`.

For example, the raw `decisions_needed` list below produces one window item titled `Choose a region`; the whitespace-padded duplicate normalizes to the same text and stable item ID:

```json
{
  "state.json": {"decisions_needed": ["  Choose a region  ", "Choose a region", "", 7, "Choose a Region"]},
  "synthesized": {"decisions_needed": ["Choose a region", "Choose a Region"]}
}
```

Deduplication is case-sensitive, so `Choose a Region` remains distinct. The original state is left as recorded. For decision window items, the trimmed decision text is used to derive the stable ID.
- **age_days** is calculated from the first 10 characters of `updated_at` (`YYYY-MM-DD`, so a bare date is accepted) as the number of days since that date, relative to `today`. Non-parseable dates result in None; a future date gives a negative value.
- **deferrals** is the project snooze count, supplied as an input by the project integration and defaulting to 0 when unavailable; it is included in the synthesized result.

### Suggested Next Action

`suggested_next_action` is None unless the chosen `next_action` is vague (see `vague_next_action` below). For a vague next action it is the first concrete (non-vague) entry from `current_priorities`, then from `delegable_work`, or None if neither has one. The suggestion is reported only; nothing writes it to state.

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
- **vague_next_action**: Set when the chosen `next_action` is a placeholder in `VAGUE_ACTIONS` or a short “work on / continue with / look into ... X” phrase (prefix plus at most 3 words), as decided by `is_vague_action()`.
- **repeatedly_deferred**: Set when the project's `deferrals` count is greater than or equal to `REPEATED_DEFERRAL_THRESHOLD` (3).

## Decisions vs. Delegable Work

- **decisions_needed**: Items requiring user decision-making. The project is waiting on the user to make a choice (e.g., "Should we rewrite the API?" or "Which platform should we target?").
- **delegable_work**: Work agents can execute autonomously without user involvement (e.g., "Write unit tests", "Refactor logging").

`delegable_work` is reported as recorded; the engine does not compute whether a project can proceed without the user. A project with `decisions_needed` gets the `needs_decision` flag.

## Scanning Projects

`scan(states, *, today, stale_days=30, include_inactive=False, deferrals=None)` scans a list of project states and returns aggregated results:

- **include_inactive**: If False (default), only projects with `status == "active"` are scanned. If True, all projects are included. Entries that are not dicts are skipped.
- **deferrals**: Optional mapping of project ids to snooze counts; missing ids default to 0.
- **projects**: List of results from `project_next_action` for each scanned project, sorted by project id.
- **stalled**: List of project ids with the `stalled` flag set.
- **no_next_action**: List of project ids with the `no_next_action` flag set.
- **needs_decision**: List of project ids with the `needs_decision` flag set.
- **blocked**: List of project ids whose normalized `blockers` or `waiting_on` lists are nonempty. It follows project-id ordering and the `include_inactive` filtering above; it is an empty list when no scanned projects qualify.
- **vague_next_action**: List of project ids with the `vague_next_action` flag set.
- **repeatedly_deferred**: List of project ids with the `repeatedly_deferred` flag set.
- **stale_days**: The threshold used for staleness detection.

`project-scan` and `executive_projects.scan` expose this additive `blocked` field through their existing scan-result forwarding. The summary contains project identifiers, while dependency details remain in each entry in `projects`, as in this example:

```json
{
  "blocked": ["alpha", "beta"],
  "projects": [
    {"project": "alpha", "blockers": ["API review"], "waiting_on": []},
    {"project": "beta", "blockers": [], "waiting_on": ["Design approval"]}
  ]
}
```

This adds no writes or commands.

The scan result allows quick identification of projects in specific conditions (e.g., all stalled projects, all projects awaiting decisions).

The Executive window projects provider emits a score-1 `project_vague_next_action` item for projects flagged with `vague_next_action`.

## Default Constant

**STALE_DAYS_DEFAULT**: 30 days. Projects not updated within this period are flagged as stalled.

## CLI Commands

### `agent-os executive project-next <project>`

Get the next action and full synthesized metadata for a specific project.

Arguments:
- `<project>`: Project identifier (e.g., `personal-agent-os`).

Options:
- `--stale-days N`: Staleness threshold in days (default 30, `STALE_DAYS_DEFAULT`).
- `--today YYYY-MM-DD`: Reference date for age calculation (default: today).

Prints the `project_next_action` result as JSON, including the project's deferral count.

### `agent-os executive project-scan [--all]`

Scan all active projects (or all projects with `--all`) and return aggregated status.

Options:
- `--all`: Include inactive projects.
- `--stale-days N`: Staleness threshold in days (default 30).
- `--today YYYY-MM-DD`: Reference date for age calculation (default: today).

Prints the `scan` result plus `errors` for projects whose state could not be loaded. Registry entries without a `state_file` are skipped.

## MCP Tools

The per-project Next Action Engine is exposed to Claude models through read-only MCP tools.

### `executive_projects.next`

Parameters: `project` (required), optional `stale_days`. Returns the same result as `project-next`, for today's date. An unknown project or one without a state file is an error.

### `executive_projects.scan`

Parameters: optional `stale_days` and `include_inactive`. Returns the same result as `project-scan`, including `errors`, for today's date.

## Executive Window Actions

Project actions in the Executive window are available through the window registry's preview/Confirm flow. Both state-changing actions below write only through this flow.

- **`project.resume`**: Returns a read-only resumption packet for the project; available for all project items: `project_decision`, `project_stalled`, `project_no_next_action`, `project_vague_next_action`, `project_repeatedly_deferred`, and `project_blocked`.
- **`project.set_next_action`**: Available for `project_stalled`, `project_no_next_action`, `project_vague_next_action`, `project_repeatedly_deferred`, and `project_blocked` items. Takes the `next_action` parameter. Empty or vague text is rejected using `is_vague_action()`. Preview shows the before and after values. Confirm writes `next_action` and `updated_at` to the project's `state.json`.
- **`project.resolve_decision`**: Available for `project_decision` items whose context carries the project and decision text. Takes the `resolution` parameter. Preview shows the proposed change; Confirm removes that decision from `decisions_needed`, appends `{decision, resolution, resolved_on}` to the optional `decisions_resolved` state field, and sets `updated_at`. The action matches the decision text exactly as stored in `state.json`; a whitespace-padded entry must be cleaned in the project state before it can be resolved using the trimmed text shown in the normalized window item. The action errors if the decision is no longer open.

## Repeated Deferrals

Deferral counts come from identifiers-only `task.deferred` Event Bus events published when Executive window items are snoozed. `window_queue.project_deferral_counts` sums these events per project using window item ids of the form `project:<pid>:...`. The `project-next` and `project-scan` CLI commands and the `executive_projects.next` and `executive_projects.scan` MCP tools apply these counts automatically, falling back to 0 when the event log is unavailable.

The Executive window `projects` provider applies the same counts and emits a score-2 `project_repeatedly_deferred` item.
