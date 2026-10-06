# Executive capture and rescue

This guide describes the deterministic capture, knowledge-gap, rescue, and project-resumption flows exposed by `agent-os executive`.

## Brain dump capture

`agent-os executive brain-dump [text] [--file PATH] [--stage-candidates PROJECT]` accepts optional positional text or reads UTF-8 text from `--file`. One of text or `--file` is required. It segments the dump into sentence-sized pieces, classifies each piece, resolves project names/aliases against the canonical project registry, and emits JSON containing `records`, `duplicates`, and `clarifications`.

Record types are `task`, `idea`, `reminder`, `appointment`, `decision`, `project_update`, `research_request`, and `follow_up`. Classification uses ordered phrase rules. Records carry a stable `bd-…` id, type, text, resolved project (or null), and confidence: 0.9 when the project resolves and 0.5 otherwise.

Repeated normalized type/text within the same dump yields a duplicate with reason `repeated_in_dump`; IDs supplied as previously captured yield `already_captured`. The first matching occurrence is retained as a record. When project resolution reports `ambiguous_project` or `unknown_reference`, the record is retained and a `clarification` entry describes its `record_id`, text, reason, and matching project candidates. No clarification is emitted merely because a segment has no project reference.

With `--stage-candidates PROJECT`, each emitted record is represented as a `preference_candidate` and passed to `agent_os.candidates.stage_candidates`. Staging is reviewable and deduplicated; it never promotes a candidate. Promotion requires curator action.

## Brain dumps in the Executive window

The window's Brain dump box posts text to `/api/brain-dump`. Records are saved in `<window home>/brain-dump.json`; repeats found in the existing capture store are reported as `already_captured`. Open records appear as `brain_dump_record` or `brain_dump_clarification` window items from the `brain_dump` provider. The `brain_dump.clarify` action sets the record's project. The `brain_dump.stage_candidate` action previews a `preference_candidate`; it stages that candidate only after the operator selects Confirm. Nothing is promoted automatically.

## Knowledge gaps

`agent-os executive gaps GAPS_JSON [--budget N] [--min-score SCORE] [--asked-id ID]` accepts a JSON list inline or from a file path. The score is the weighted sum of factors clamped to 0–1: utility 0.35, recurrence 0.20, confidence_gap 0.25, and urgency 0.20; interruption_cost and sensitivity each subtract up to 0.50. Missing or invalid factors contribute zero. Scores are rounded to four decimals.

Results include `ask`, `deferred`, `discarded`, and `budget`. Eligible questions sort by descending score and then ID. `budget` caps `ask`; eligible overflow is deferred with reason `over_budget`. Previously asked IDs are discarded as `already_asked`, and scores below `min-score` as `low_value`. Each result item includes `id`, `question`, `topic`, `score`, `why`, and `reason`. The `why` field shows the score and up to three strongest positive raw factor values, plus any applied penalties.

## Knowledge gaps in the Executive window

`agent-os executive gaps <json> --enqueue [--tab work|personal]` persists gaps to `knowledge-gaps.json` in the window home. The `knowledge_gaps` provider displays up to three selected questions (`select_questions`), excluding already-answered gaps, as `knowledge_gap_question` items. The `knowledge_gap.answer` action accepts `answer` and `project`, previews the candidate built by `answer_to_candidate`, and stages it only after Confirm. The gap is then marked answered; nothing is promoted.

## Rescue mode

`agent-os executive rescue [--tab work|personal] [--today DATE] [--stale-days N] [--horizon-days N]` considers executive queue items and project next-action results. Its basis order is:

1. `deadline`: highest-ranked queue item with a due date on or before today plus the horizon.
2. `project`: an active, unblocked project with a concrete next step (or suggested step for a vague action). Projects needing a decision sort after other eligible projects; older state sorts first, then project ID.
3. `queue`: the top ranked queue item when no deadline or eligible project took priority.
4. `null`: nothing available.

The result includes `mode`, `basis`, one `action` (title, project, queue item ID, due date), a short `why`, the number of `suppressed` alternatives, and a `then` instruction to finish one step and run rescue again. Queue and project loading errors are reported alongside the result.

## Rescue mode in the Executive window

The window's Rescue toggle (`rescue-toggle`) calls `GET /api/rescue?tab=work|personal[&horizon_days=N]`. The route runs `rescue_view.rescue_view` over the same window queue (`registry.queue`) and canonical project next actions (`rescue_view.project_results`), which is also used by `agent-os executive rescue`. The response contains the rescue result plus `item_id`, `tab`, and `errors`. `item_id` identifies the window item for a deadline or queue action; it is null for a project action or when there is no action.

The window shows only the selected item, with its normal options and preview/Confirm flow, alongside the `why` and `then` text and the count of suppressed alternatives. The route is read-only.

## Project resumption packet

`agent-os executive resume PROJECT [--today DATE] [--stale-days N]` resolves and loads the project state and returns a compact packet with schema `resumption-packet@1` (`agent-os/resumption-packet@1`). The packet fields are `schema`, `project`, `status`, `goal`, `where_you_left_off`, `next_action`, `next_action_source`, `open_loops`, `age_days`, `flags`, and `truncated`. `open_loops` contains `blockers`, `waiting_on`, and `decisions_needed`. Text is limited to 280 characters by default, each open-loop list to three items; `truncated` reports when content was shortened or omitted. A suggested action is surfaced when project analysis marks the stored next action as vague.

## Resumption packets in the Executive window

Project items from the `projects` provider with kinds `project_decision`, `project_stalled`, `project_no_next_action`, and `project_vague_next_action` offer the `project.resume` (Resume) option. This action is read-only and not consequential, so it has no preview/Confirm step. It is implemented in `agent_os.executive.window.actions_projects`. The action loads the project's state and returns `{project, packet}`, where `packet` is the same `resumption-packet@1` produced by `agent-os executive resume`. The window shows a summary of the goal, where you left off, the next action and its source, any non-empty open loops, the age, and whether the packet was truncated.

## Not yet implemented

- MCP exposure for these capture and rescue commands.
- Calendar or voice input.
- Model-based extraction; brain-dump segmentation, classification, and project resolution use deterministic rules.
- Staging knowledge-gap answers directly from the CLI; answers are staged only through the window `knowledge_gap.answer` action.
