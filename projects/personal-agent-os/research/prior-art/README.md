# Open-source prior art

Before Orchestrator builds or significantly expands a subsystem, check whether
the problem has already been solved well in the open. The goal is to reduce
duplicated engineering. Agent OS stays the canonical, provider-independent
architecture.

- Registry: [`registry.json`](registry.json) (entries follow `schemas/prior-art-entry-v1.schema.json`, prefix `PA-`).
- Tool: `agent-os orchestrate prior-art lookup|queries|stale|refresh` (`src/agent_os/orchestrator/prior_art.py`, no model call).
- Rules: `policy/orchestrator-os.policy.json` → `prior_art`.

## When a check is required (proportional)

| Change | Check |
|---|---|
| Small fix, utility, or change inside an existing module (< ~150 lines, no new concept) | none |
| New module or capability, new dependency, or a subsystem > ~150 lines | **light**: `prior-art lookup "<problem>"`, read matching entries, note the result in the IMP/DEC |
| New subsystem or architecture, a repeatedly failing subsystem, a proposed dependency, or a simplification candidate | **full**: light check + `prior-art queries "<problem>"` → search → inspect 2–5 candidates (code **and** tests) → add or update entries → decide |

A check that finds an entry evaluated within its staleness window reuses that entry. It does not search again.

## Decision chain

```
PROBLEM → EXISTING AGENT OS CAPABILITY → PRIOR-ART LOOKUP → CANDIDATES
→ ADOPT | WRAP | BORROW | REJECT | DEFER | INVESTIGATE → IMPLEMENTATION DECISION
→ EXPERIMENT (incumbent vs candidate) → EVALUATION (EVR) → DEC
```

The resulting DEC or IMP states a `prior_art` note covering what was checked, what was found, what was reused, and, if nothing was reused, why custom code is still necessary. `agent-os validate` warns when a new DEC lacks it.

Research alone never promotes a dependency. ADOPT, WRAP and BORROW enter code only through the normal IMP → HYP → EXP → EVR → DEC chain. An ADOPT entry must link an EVR, EXP or DEC.

## Choosing a decision

The operator's preference (2026-09-29) is to **subsume rather than depend**. Borrow or vendor the needed algorithm, pattern, tests or schema, with attribution, instead of adding a package. Agent OS has one runtime dependency (`keyring`), and that is deliberate.

- **BORROW**: a small algorithm, pattern, schema or test set gives most of the value. This is the default for useful projects.
- **WRAP**: the project supplies a strong, replaceable capability that is too large to subsume (for example a sandbox or eval runtime). Put it behind an Agent OS adapter as an optional extra that can be removed.
- **ADOPT**: owning equivalent code would clearly be wasteful and evidence shows the gain. Keep it rare.
- **REJECT**: integration or coupling costs more than the demonstrated value, or the project conflicts with Agent OS boundaries.
- **DEFER**: promising but premature. State the trigger that would reopen it.
- **INVESTIGATE**: plausible value that needs a spike or benchmark before any decision.

Challenge every potential dependency on:
- dependency weight and transitive count
- maintenance activity
- license
- security history
- API stability
- provider, storage and cloud assumptions
- runtime overhead
- observability
- portability
- how hard it would be to remove

Keep the evidence dimensions separate: development savings, runtime savings, quality, reliability, security, complexity, maintenance, portability. Do not claim a saving that you haven't inspected enough code to justify. Say `unknown` instead.

## Boundaries

External projects never become canonical memory, project state, the authorization or promotion authority, a protected evaluator, or a provider-specific source of truth. Agent OS must always be able to replace them.

Their **tests** are often worth more than their code. When inspecting a project, look at its unit, integration, adversarial, state-machine and benchmark fixtures. Where useful, adapt cases into `projects/personal-agent-os/orchestrator-os/evals/` with provenance, keeping them out of protected holdouts unless the operator places them there.

## Discovery: task-specific, event-driven

Run discovery when:
- a new subsystem is proposed;
- an existing subsystem underperforms or fails repeatedly (FAIL recurrence);
- implementation cost is high;
- the simplification engine finds custom infrastructure that may be replaceable, or a dependency Agent OS no longer needs;
- a dependency goes stale or has a security or license event;
- a new model or provider capability appears;
- a research item (RAD) points to a new technique;
- an agent meets a problem with no known solution.

Derive queries from the gap (`prior-art queries "<problem>"`). Prefer primary sources: the project repository, official docs, and the paper with its code. Record provenance in each entry: the URLs and API calls used.

## Refresh

Don't re-check everything on a schedule. `prior-art stale` lists entries past their window: INVESTIGATE 30 days, DEFER 120, ADOPT and WRAP 180, BORROW and REJECT 365, or an explicit `revisit_by`. Each entry's `revisit_when` names its event triggers (major release, unmaintained, security issue, license change, Agent OS capability change, competitor, repeated local failure). `prior-art refresh <ids> --write` updates activity facts from the GitHub API deterministically.

## Links into meta-improvement

Entries link to IMP, HYP, EXP, EVR, DEC, CAP, FAIL, SUC and RAD records by id. For example:

```
RAD (new router found) → FND (supports uncertainty-aware routing) → IMP (evaluate vs Agent OS router)
→ HYP (threshold method cuts cost without reliability loss) → EXP → EVR → DEC (BORROW algorithm / REJECT project)
```

The simplification engine (MIE-0011) consults this registry in both directions. It flags large custom code that a mature, light project could replace (an ADD or BORROW candidate), and dependencies Agent OS has outgrown (a REMOVE candidate).
