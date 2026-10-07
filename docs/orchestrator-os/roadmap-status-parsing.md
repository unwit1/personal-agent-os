# ORCH-A / IMP-0034 roadmap status parsing before/after report

This report compares HEAD’s old `classify()` with the checked-out new `classify()` by extracting `classify()` and `parse()` from `git show HEAD:src/agent_os/orchestrator/roadmap.py` and importing `src/agent_os/orchestrator/roadmap.py`; the exact command used was `python $env:TEMP\roadmap_status_before_after.py`.

## Agent OS master roadmap

| stage id | title (short) | old status | new status | changed | status line (truncated to 120 chars) |
|---|---|---|---|---|---|
| P0.0 | Universal Agent OS routing for chats and work proj | complete | complete | no | Status: **complete** (2026-09-21). All acceptance criteria met and covered by |
| P0.0A | Unified Connector Broker + cross-surface auto-prov | deferred | deferred | no | Status: **on hold** (2026-10-04), awaiting operator decisions: the launch command written into native |
| P0.1 | Staged Workflow Orchestrator + next-prompt/model h | complete | complete | no | Status: **complete** (2026-09-21). Manifest schema, stage lifecycle, persisted |
| P0.2 | Selective context and profile retrieval | complete | complete | no | Status: **complete** (2026-09-21). EXEC-0.5 is implemented in |
| P0.3 | Shared document intelligence + local persistent ex | deferred | deferred | no | Status: **on hold here** (2026-10-04): the Agent OS side is complete and covered by consumer-contract tests; the remaini |
| P0.4 | Resumable/checkpointed ingestion everywhere | deferred | deferred | no | Status: **on hold** (2026-10-04), awaiting operator decisions: every safe local/fixture seam is already wired to the ing |
| P0.5 | Deterministic/cache/skill-first execution policy | complete | complete | no | Status: **complete for now** (2026-10-04). Deterministic-first selection with evidence-triggered model |
| P0.6 | Skill/Economy Regression Test Suite | complete | complete | no | Status: implemented with a deterministic, privacy-safe fixed corpus, context |
| P1.1 | Privacy-safe usage telemetry | deferred | deferred | no | Status: **on hold** (2026-10-04), awaiting an operator decision on chat-session telemetry capture (whether and how Claud |
| P1.2 | Adaptive router | complete | complete | no | Status: **complete** (2026-10-04). Provider-neutral capability classes, |
| P1.2A | Multi-agent coding orchestrator + control GUI | complete | complete | no | Status: **implemented, first release** (2026-09-22, merged to `main`; see |
| P1.3 | Optional API delegation | deferred | deferred | no | Status: **on hold** (2026-10-04), awaiting operator decisions: whether engine runs may route Agent-OS-owned subtasks to  |
| P2.1 | Automation Miner | complete | complete | no | Status: **complete for now** (2026-10-05); the larger import-loop extraction is on hold for an architectural decision. E |
| P2.2 | Skill Miner | deferred | deferred | no | Status: **deferred** pending a reviewed deterministic skill-runner contract and |
| P2.3 | Prompt/context optimization | complete | complete | no | Status: **complete for now** (2026-10-05). The offline measurement and gating tools, lossless handoff compaction and opt |
| P3 | Executive Core | in_progress | in_progress | no | Status: **in progress** (2026-10-06). EXEC-0 entity, event, and queue-item schemas and contracts are present, with deter |
| P4 | Capture, memory refinement, and Rescue Mode | complete | complete | no | Status: **complete for now** (2026-10-06); remaining inputs belong to later stages (calendar/commitments P6, voice P7, m |
| P5 | Attention, delegation, and daily brief | not_started | not_started | no |  |
| P6 | Life and communication integrations | not_started | not_started | no |  |
| P7 | Proactivity and voice | not_started | not_started | no |  |
| P8 | Controlled autonomy | not_started | not_started | no |  |
| P9:reusable-knowledge-libra | Reusable Knowledge Library subsystem | not_started | not_started | no |  |
| EXEC-15 | Lorekeeper / Creative Intelligence | not_started | not_started | no |  |

Changed rows:
- None; every parsed stage retained its classification.

## ingester-engine ROADMAP.md

| stage id | title (short) | old status | new status | changed | status line (truncated to 120 chars) |
|---|---|---|---|---|---|
| P0.1 | Program baseline and orchestrator preflight | complete | complete | no | Status: Benchmark script, baseline results, conformance matrix, and parity test implemented and passing (tests/test_conf |
| P0.2 | Centralization inventory verified | complete | complete | no | Status: **complete**. `docs/plans/centralization-map.json` (merged from 8 shards in `docs/plans/centralization-map.d/`)  |
| P1.1 | Config v2 | complete | complete | no | Status: **complete**. Config v2 parser (`parse_config_toml` and `load_config_toml` in `src/ingester_engine/config_toml.p |
| P1.2 | Plugin host and the core pack | not_started | not_started | no |  |
| P1.3 | Composable profiles and routes | not_started | not_started | no |  |
| P1.4 | Packaging, doctor, and pin enforcement | not_started | not_started | no |  |
| P1.5 | EPUB adapter and fiction structure candidates | not_started | not_started | no |  |
| P1.6 | Readable source layout and storage economy | not_started | not_started | no |  |
| P1.7 | Source checklist and inbox | not_started | not_started | no |  |
| P1.8 | Universal scan, categorization, and adapter scaffo | not_started | not_started | no |  |
| P2.1 | Analysis adapter contract and job phase | not_started | not_started | no |  |
| P2.2 | Model backends and cost ledger | not_started | not_started | no |  |
| P2.3 | First interpretive lenses with a gold evaluation | not_started | not_started | no |  |
| P2.4 | Remaining fiction lenses and revision alignment | not_started | not_started | no |  |
| P3.1 | Corpus-lens contract, scopes, and authority ladder | not_started | not_started | no |  |
| P3.2 | Resolver framework | not_started | not_started | no |  |
| P3.3 | Review queue and promotion | not_started | not_started | no |  |
| P3.4 | Research connectors and saturation | not_started | not_started | no |  |
| P3.5 | Wiki discovery and bulk wiki crawling | not_started | not_started | no |  |
| P3.6 | Valid-time scopes and catalog connectors | not_started | not_started | no |  |
| P4.1 | Asset object model and blob store | not_started | not_started | no |  |
| P4.2 | Vision pack | not_started | not_started | no |  |
| P4.3 | Audio and video pack | not_started | not_started | no |  |
| P4.4 | 3D pack | not_started | not_started | no |  |
| P4.5 | Bethesda pack | not_started | not_started | no |  |
| P5.1 | Query API and vector search | not_started | not_started | no |  |
| P5.2 | Style, voice, and art cards | not_started | not_started | no |  |
| P5.3 | Replication evaluation harness | not_started | not_started | no |  |
| P5.4 | ML exports | not_started | not_started | no |  |
| P6.1 | Agent OS service surface | not_started | not_started | no |  |
| P6.2 | Templates, conformance levels, adoption | not_started | not_started | no |  |
| P7.1 | RTEC-HR | not_started | not_started | no |  |
| P7.2 | Elder Scrolls | not_started | not_started | no |  |
| P7.3 | Brickmen | not_started | not_started | no |  |
| P7.4 | Speech and personal archives | not_started | not_started | no |  |
| P7.5 | HR-GUI scanner | not_started | not_started | no |  |
| P7.6 | Cosmere | not_started | not_started | no |  |
| P7.7 | mtgBot and media-intake-prototype | not_started | not_started | no |  |
| P8.1 | Pack SDK | not_started | not_started | no |  |
| P8.2 | Encrypted containers and scale | not_started | not_started | no |  |

Changed rows:
- None; every parsed stage retained its classification.
