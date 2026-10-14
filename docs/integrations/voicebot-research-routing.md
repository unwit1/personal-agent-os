# Voicebot research and Orchestrator integration pointer

**Date:** 2026-10-14. **Status:** researched/queued; no running service or benchmark claimed. **Canonical domain:** [unwit1/voicebot](https://github.com/unwit1/voicebot). **Skyrim consumer:** [unwit1/sse-modforge](https://github.com/unwit1/sse-modforge).

## Why this pointer exists
Voicebot owns reusable voice synthesis, cloning for authorized speakers, fictional VoiceType design, speech editing/splicing, model adapters, voice-data QC, lexical/prosody/emotion/naturalness measurement, calibrated speaker/voice-type evaluation, audio artifact and experiment lineage. SSE ModForge must use Voicebot to **generate, inspect, objectively evaluate and repair all voice files** while retaining Skyrim record extraction, game-native LIP/XWM/FUZ packaging and in-game testing. Agent OS/Orchestrator remains the globally canonical scheduler, GPU broker, permission/cost gate and cross-project context manager.

**Do not duplicate model catalog, speaker recordings, raw audio, GPU broker, evaluators or private datasets into this repository.** Fetch only relevant versioned Voicebot capability records and cost/performance evidence by task, preserving consent/source and project boundary.

## Where to continue
- [Voicebot readme](https://github.com/unwit1/voicebot/blob/main/README.md), [checkpoint](https://github.com/unwit1/voicebot/blob/main/STATE.md) and [implementation roadmap](https://github.com/unwit1/voicebot/blob/main/ROADMAP.md).
- [2026-10-14 independent model comparison](https://github.com/unwit1/voicebot/blob/main/research/FRONTIER_AND_INDEPENDENT_EVIDENCE_2026-10-14.md): **VOICE-H** human preference and **Hume** clone identity tested separate; VoiceMOS, RVCBench and AudioJudge; Fish Drama 3 (October 13, 2026 release); VoxCPM2, LongCat AudioDiT, Qwen3, ZONOS2, Higgs v3 and other current candidates; rights warnings.
- [Orchestrator staged execution playbook](https://github.com/unwit1/voicebot/blob/main/docs/ORCHESTRATOR_RESEARCH_EVAL_AND_OPTIMIZATION_PLAYBOOK.md): context-minimal task specialists, job DAG, quality gates, compute, model routing, $/accepted minute, resumption and failure.
- [Evaluation meta-bench](https://github.com/unwit1/voicebot/blob/main/evaluation/EVALUATOR_META_BENCHMARK_AND_REPAIR_POLICY_2026-10-14.md): calibrate judges against people, timestamped defects, separate voice-type and authorized speaker, no misleading percentage likeness.
- [Training and serving source radar](https://github.com/unwit1/voicebot/blob/main/research/SERVING_TRAINING_DATA_AND_SOURCE_RADAR.md): vLLM-Omni, SGLang-Omni, Runpod, checkpoint and dataset tooling, licensing, optimization trials and acquisition wishlist.
- [Voicebot-to-ModForge service contract](https://github.com/unwit1/voicebot/blob/main/docs/MODFORGE_CONSUMER_CONTRACT.md) and [ModForge implementation handoff](https://github.com/unwit1/sse-modforge/blob/main/integration/VOICEBOT_SKYRIM_HANDOFF.md).

## Recommended first Orchestrator job
Read Voicebot README/STATE/ROADMAP; inspect current state and any concurrent agent work; make a small scoped implementation plan; validate JSON/CI; select one local/open TTS challenger with weights/code/license approved and a fictional synthetic voice target; run offline smoke generation and at least one **independent** audio scorer. Use a fixed original short script + rights-cleared reference and record raw audio/score manifests in private store. Compare alternate candidate and cost, add human A/B; only then implement costed Runpod or managed API benchmarks. No model inference has been completed as part of research and no spend is authorized by this document.

## Model research and budget separation
The [Model Infrastructure Manager](../../projects/personal-agent-os/roadmap/model-infrastructure-manager.md) is already responsible for Runpod/provider-neutral resource planning, permission approvals, budgets and capabilities. Do not construct a second GPU resource scheduler in Voicebot; the voice-specific adapter integrates with it. Source research gives priors, measured Voicebot local results govern task routing once available. Audits must record model checkpoint/license, input source+consent, role and project privacy, evaluator version, hardware/cost, stratified quality and exact reproducibility.

## Planned compatibility boundaries
- Expose versioned `voice.capabilities`, `voice.generate`, `voice.evaluate`, `voice.repair`, `voice.model.benchmark`, `voice.artifact.resolve`; these are **planned names** until an implementation exists, not currently callable functions.
- Never auto-use private Ambient Capture microphones/voiceprints as clone training. Voice owner authorizes that use separately.
- Missing code/backend/permission must return `not_run`, `blocked` or `unavailable`, not made-up pass.
- ModForge's game-native compilation is downstream. Evaluate **final FUZ-decoded audio** in Voicebot to catch codec degradation while ModForge checks lip and game FormID/VoiceType mapping.
- No model self-promotion, secret access expansion, cloud upload or billable GPU without an explicit approved policy; continue safely with original assets on failure.

## Continuous research/watch candidate
WatchBot can periodically track upstream changes for frontier model families, independent human evaluation, voice-score meta-evals, Runpod costs, security and restrictive licenses. New versions become benchmark *candidates*, not automatic replacement of stable routes. Do not create a subscription task until operator requests it.

## October 14, 2026 — open-source trainer acquisition and Orchestrator jobs

New [Voicebot 39-tool training survey](https://github.com/unwit1/voicebot/blob/main/research/OPEN_SOURCE_VOICE_TRAINING_ECOSYSTEM_2026-10-14.md), [machine-readable source catalog](https://github.com/unwit1/voicebot/blob/main/research/OPEN_SOURCE_TRAINING_COMPONENTS_2026-10-14.json) and [trainer science / experiment handoff](https://github.com/unwit1/voicebot/blob/main/research/VOICE_TRAINING_ENGINEERING_ABLATIONS_AND_ORCHESTRATOR_HANDOFF.md). The [Voicebot Orchestrator workplan](https://github.com/unwit1/voicebot/blob/main/plans/ORCHESTRATOR_RESEARCH_WORKPLAN_2026-10-14.json) now has **18 not_run jobs**, including canonical training dataset, VoxCPM2/Qwen3 trainer adapters, RVC/Applio conversion, checkpoint ablations and preference optimization. This is **research, not deployed code**.

The Agent OS Model Infrastructure Manager stays owner of Runpod/cloud account, model/GPU budgets and worker spawning. Voicebot owns audio preparation, training recipes, acoustic scoring, model-specific adapters and reproduction. Avoid copying the 39-model catalog into Agent OS; link/retrieve relevant source rows only. The user's academic code reuse grant still requires tracking upstream revisions/weights/third-party library conditions; never move personal recordings to another provider without explicit approved scope and spend policy.
