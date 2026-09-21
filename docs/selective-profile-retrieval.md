# Selective profile retrieval

Status: implemented (P0.2 / EXEC-0.5)

## The problem

Durable personal context is useful precisely because it is always available —
and useless if answering "fix a scanner bug" also loads meal planning, leisure
interests, and every stored preference. Before this, `profile/` was effectively
unwired: only `preferences.json` reached the lexical index, and the context
compiler never injected profile context at all. The only alternatives were
"nothing" or "everything".

Injecting everything would cost roughly **16,878 tokens** per request.

## The approach

The profile is flattened into individually addressable **facts**, and only the
slice a task actually touches is compiled in.

Each fact carries:

| field | meaning |
|---|---|
| `id` | stable, content-addressed from source + path |
| `domain` | topical section (`work_context`, `household_planning`, …) |
| `statement` | the readable fact |
| `confidence` | `stated` > `seeded` > `derived` |
| `provenance` | which sources asserted it |
| `sensitivity` | `personal` or `restricted` |
| `updated_at` | recency, used to break ties |

### Sources

Canonical: `profile/preferences.json`, `profile/user-context.json`.

`profile/drive-derived-context.json` is **deliberately excluded**. It is a
60 KB derived index, not curated durable context, and loading it would
reintroduce exactly the bulk this module exists to prevent. A test asserts it
never appears in the index.

## Three rules

**Relevance is earned, not assumed.** A fact enters a packet only above a
relevance floor *and* with a distinctive signal: either domain vocabulary or
more than one matched term. One shared generic word is coincidence, not
evidence — "rename a **variable**" must not pull in a fact about housing being
"variable". This mirrors the distinctive-signal rule the project router already
applies.

A task with no personal dimension therefore retrieves **nothing at all**.

**Provenance survives.** An explicit user statement is distinguishable from
something inferred from a scan, and when two facts overlap, the stronger record
wins — then the newer one. The superseded fact is reported in diagnostics
rather than silently vanishing.

**Privacy is enforced at retrieval, not at authorship.** The `privacy` section
is never retrievable, and any fact tripping the privacy gate (email, SSN,
phone, secrets, paths) is dropped regardless of what is on disk. No caller can
reach restricted material by forgetting to filter. `agent.py validate` fails if
a retrievable fact carries a privacy finding.

## Diagnostics

Every retrieved fact explains itself — which terms matched and which domain
vocabulary fired — and the diagnostics block reports how many facts were
indexed, considered, selected, and deduplicated, along with the thresholds
used. This is an audit trail of retrieval, not a window into hidden reasoning.

## Commands

```powershell
agent-os profile-status
agent-os profile-retrieve "plan meals and groceries for next week"
agent-os profile-retrieve "hr scanner ocr" --limit 3 --minimum-score 6
```

Over MCP: `profile.retrieve` and `profile.status`, so every routed surface uses
the same canonical retrieval path.

The context compiler attaches a `profile_context` section automatically when a
task earns one, so a task receives relevant personal context **without asking
for a profile file**. When budget pressure prunes the slice to nothing, the
whole section is dropped — an empty diagnostics shell is pure overhead.

## Measured behaviour

Profile on disk: 105 facts indexed, 93 retrievable, 12 restricted.

| task | facts | tokens | domains |
|---|---|---|---|
| fix the HR scanner OCR accuracy for personnel forms | 5 | ~293 | `work_context` |
| plan meals and groceries for next week | 5 | ~332 | `household_planning` |
| track bills and spending this month | 2 | ~158 | `financial_assistant_goals` |
| rename a variable in a python function | 0 | 0 | — |

Against ~16,878 tokens to inject the profile whole, that is a **98%+
reduction** on personal tasks and complete absence on impersonal ones.

## Known limits

- Relevance is lexical and vocabulary-driven. A task phrased entirely in
  synonyms the domain vocabulary does not know will retrieve nothing. That
  fails closed, which is the right direction, but it does mean
  `DOMAIN_TERMS` needs curation as the profile grows.
- Candidate profile updates still flow through the existing candidate pipeline;
  there is no profile-specific promotion rule yet.
- Facts inherit their source file's `updated_at` and provenance. Per-fact
  confirmation dates are not tracked, so "last confirmed" is file-level.
