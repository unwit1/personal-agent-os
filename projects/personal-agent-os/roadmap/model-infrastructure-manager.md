# Model Infrastructure Manager / Compute Broker

Status: **operator-requested, high priority**  
Owner: Orchestrator OS / Personal Agent OS  
Tracked improvement: **IMP-0015**  
Requested: 2026-09-29

## Goal

Build one provider-neutral control plane that lets Orchestrator select, acquire,
run, evaluate, train, and retire model compute without requiring the operator to
research individual releases, providers, GPU SKUs, serving stacks, or model
families by hand.

The subsystem must be plug-and-play across current and future model releases.
Models are temporary capabilities; Orchestrator owns the durable capability,
cost, provenance, evaluation, budget, and routing state.

The implementation must support, through the same high-level broker:

- subscription/seat-backed models where an approved integration exists;
- direct model APIs;
- open-weight/self-hosted models;
- low-refusal / abliterated open-weight variants;
- temporary cloud GPU pods;
- scale-to-zero/serverless GPU endpoints;
- image generation and image editing models;
- multimodal models;
- voice/audio models;
- model training/fine-tuning jobs, including LoRA/adapters;
- embeddings, classifiers, and other ML workloads;
- future model modalities without redesigning Orchestrator.

RunPod is the first cloud-compute adapter, **not** the architecture boundary.

## Non-goals and invariants

1. Never hard-code Orchestrator around one vendor, model family, GPU provider,
   serving framework, or modality.
2. Never put provider credentials, payment credentials, raw secrets, private
   datasets, or private model artifacts in Git.
3. An experimental/abliterated model may plan and route, but it is not the sole
   authorization boundary. Consequential writes, spending, secret access, and
   destructive operations remain deterministically gated.
4. Context minimization is required; context laundering is not. Workers should
   receive the smallest truthful Task Context Contract needed for their job.
   Do not intentionally remove facts that materially change the safety or
   authorization meaning of an operation.
5. Open/abliterated models may be preferred for legitimate workloads where low
   refusal behavior, privacy, reproducibility, or self-hosting is materially
   useful. Subscription models should continue to handle benign/non-sensitive
   work when they are the cheapest reliable route.
6. No paid cloud job or material training run starts merely because a model
   proposes it. Budget policy and approval gates are authoritative.
7. Research claims and public benchmark results are priors. Agent OS's measured
   task-family evidence should dominate routing once enough samples exist.

## Architecture

```text
Task / Project Goal
        |
        v
Model Infrastructure Manager
        |
        +-- Capability Registry
        +-- Model Research Radar
        +-- Workload Profiler
        +-- Task Context Contract builder
        +-- Route / Foreman planner
        +-- Cost & Budget Engine
        +-- Compute Broker
        +-- Training / Fine-tune Planner
        +-- Artifact & Checkpoint Registry
        +-- Evaluation / Benchmark harness
        |
        +----------------+----------------+----------------+
        |                |                |                |
        v                v                v                v
 Subscription/API   Open-weight API   RunPod / cloud   Future provider
 models             endpoints         GPU/serverless   adapter
```

Provider adapters expose capabilities. The scheduler and foreman do not contain
vendor-specific logic.

## Generic workload contract

Every execution request should normalize to a provider-neutral workload object.

Minimum dimensions:

- workload type: inference, batch inference, embedding, training, fine-tune,
  adapter/LoRA training, evaluation, conversion/quantization, or serving;
- modality: text, code, vision, image, audio/voice, multimodal, or future;
- required model capabilities and quality floor;
- tools/function calling/structured-output needs;
- context/input/output size estimates;
- privacy/sensitivity classification;
- latency, throughput, concurrency, and deadline requirements;
- minimum/recommended VRAM/RAM/storage;
- expected runtime and utilization;
- artifact/checkpoint requirements;
- licensing/redistribution/training restrictions;
- project budget, job hard cap, and approval state;
- reliability threshold and independent-verification requirement.

## Model capability registry

Track exact model/version/quantization/provider combinations rather than names
alone. Suggested fields:

```yaml
model_id:
family:
version:
revision:
provider:
deployment:
  - subscription
  - api
  - serverless
  - gpu_pod
  - local
modalities:
license:
open_weights:
alignment_profile:
  refusal_profile:
context_window:
tool_calling:
structured_output:
multimodal_inputs:
recommended_vram:
supported_precisions:
supported_quantizations:
serving_backends:
training_support:
adapter_support:
capabilities:
  coding:
  reasoning:
  planning:
  image_generation:
  image_editing:
  asr:
  tts:
  speech_to_speech:
  voice_conversion:
  diarization:
  audio_generation:
price:
latency:
throughput:
availability:
public_benchmark_evidence:
agent_os_capability_evidence:
last_verified:
provenance:
```

Do not treat "uncensored" or "abliterated" as a quality score. Record it as a
behavioral/refusal characteristic alongside measured competence.

## Abliterated / low-refusal foreman

Support an optional open/abliterated model as a Foreman candidate for:

- task decomposition into a dependency DAG;
- context packing/minimization;
- capability estimation;
- worker/model selection;
- parallelization;
- retry and refusal analysis;
- cost-aware escalation;
- review assignment.

Roll out through **shadow mode first**:

1. Current Orchestrator executes normally.
2. Foreman independently proposes a plan and route.
3. Store proposal, cost estimate, refusal behavior, predicted route, actual
   route, actual result, retries, validator result, and total cost.
4. Compare foreman decisions against the incumbent.
5. Promote routing authority only after relevant evals and shadow evidence.

Refusals are first-class telemetry. Distinguish, where evidence permits:

- unsupported capability;
- provider policy/refusal;
- malformed/ambiguous request;
- context collision from irrelevant context;
- authorization/policy restriction;
- genuine worker failure.

A benign atomic task may be retried with a smaller truthful context contract or
another eligible model. Do not use decomposition to conceal safety-relevant
facts from a worker that needs them.

## Continuous model research

The Research Radar should continuously discover and re-evaluate:

- new open-weight and proprietary model releases;
- coding/reasoning/tool-use improvements;
- open/abliterated derivatives;
- image and multimodal models;
- speech/voice/audio models;
- new quantizations and inference engines;
- LoRA/fine-tuning methods;
- new cloud/serverless GPU providers;
- provider pricing and GPU availability;
- licensing or terms changes that affect deployment/training;
- meaningful benchmark/eval changes.

For every candidate, collect source provenance, revision/date, license, modality,
hardware needs, context limits, serving compatibility, public benchmark priors,
pricing, and whether an Agent OS benchmark should be scheduled.

Use representative Agent OS workloads. Do not switch production routing because
of marketing claims alone.

## Compute Broker

RunPod is the first implementation target. Keep provider-neutral interfaces so
Vast.ai, Modal, Lambda, hosted inference vendors, or future providers can be
added without scheduler changes.

The broker must be able to:

- discover live hardware/endpoint availability and prices;
- compare API vs serverless vs temporary-pod economics;
- estimate startup/model-load overhead;
- select the cheapest configuration that clears capability/reliability needs;
- provision a pod/endpoint/job;
- attach persistent storage when justified;
- deploy an approved serving/training container;
- return a normalized endpoint/capability handle to Orchestrator;
- monitor health, utilization, runtime, and spend;
- checkpoint/resume jobs;
- handle bounded retry and spot/preemptible interruption;
- automatically scale down/stop/delete idle resources;
- reconcile estimated vs actual cost;
- retain a complete auditable lifecycle record.

Prefer OpenAI-compatible serving for text/code where practical, but do not force
image/audio/training workloads into a text API abstraction. Normalize them at
the broker/capability layer.

## Credential and secret handling

Local credential setup is explicitly allowed.

Use a secret abstraction such as:

```text
secrets://runpod/default
secrets://huggingface/default
secrets://provider/profile
```

Back it with OS keychain/keyring where available, with environment variables as
a supported fallback. Repository configuration stores only secret references.

Required behavior:

- interactive local setup/status/delete commands;
- provider-specific minimum scopes where possible;
- never echo secrets into logs/prompts;
- never commit secrets;
- redact accidental secrets from telemetry;
- keep payment-card data out of Agent OS;
- prefer provider-native account auto-pay/funding controls rather than giving a
  model raw card credentials.

## Intelligent quote and budget engine

Before any material paid workload, return a quote and execution plan. It must
include:

- recommended model/model family;
- inference vs adapter/LoRA vs full fine-tune rationale;
- required/preferred GPU class and VRAM;
- expected runtime;
- storage and bandwidth needs;
- dataset/preprocessing requirements;
- provider options;
- low / expected / high estimated cost;
- uncertainty drivers;
- cheaper alternative;
- higher-quality alternative;
- what additional budget would materially change;
- hard cap and stop condition.

Support:

- quote-only/dry-run mode;
- user-supplied project budget;
- per-job hard cap;
- per-project/monthly caps;
- budget reservation before launch;
- approval threshold for material spend;
- retry/spend ceilings;
- idle shutdown;
- cost anomaly detection;
- emergency stop/cancel.

A planner can recommend more spend but cannot grant itself a higher cap.

## Image and visual model support

Treat image workloads as first-class capabilities:

- text-to-image;
- image-to-image;
- editing/inpainting/outpainting;
- control/reference conditioning;
- multimodal understanding;
- upscaling/restoration where appropriate;
- batch generation;
- model/adapter training.

Support Stable Diffusion, SDXL, Flux-class and future architectures through
metadata/adapters rather than family-specific orchestration.

For training/adaptation, automate but audit:

- dataset inspection;
- provenance/license checks;
- deduplication;
- caption/label generation where appropriate;
- train/validation split;
- resolution/bucketing;
- base-model compatibility;
- hyperparameter proposal;
- checkpoint cadence;
- validation samples;
- overfitting checks;
- baseline comparison;
- reproducibility manifest;
- artifact export/versioning.

## Voice and audio model support

Voice/audio is a first-class modality, not an afterthought. Support current and
future providers/models for:

- ASR / speech-to-text;
- TTS / speech synthesis;
- speech-to-speech;
- voice conversion;
- speaker embeddings/verification where a project legitimately requires it;
- speaker diarization;
- speech enhancement, denoising, source separation, and cleanup;
- forced alignment / timestamping;
- pronunciation/phoneme-related models;
- audio generation and other project-relevant audio ML workloads;
- voice-model adaptation/fine-tuning/LoRA where supported.

The quote/planning system for voice projects should reason about:

- source audio duration and quality;
- sample rate/channels/codecs;
- segmentation and silence handling;
- transcript availability and alignment quality;
- speaker count/identity metadata;
- noise/reverb;
- training/validation split;
- base-model language/accent coverage;
- GPU/VRAM/runtime;
- preprocessing cost;
- inference latency/streaming needs;
- expected storage and artifact size.

Identity-linked voice training/cloning data must retain project-scoped
provenance and authorization/consent metadata when applicable. Never silently
mix one person's voice data into another project or training corpus.

## General ML training

The training planner must also cover non-generative ML where useful:

- embeddings;
- classifiers;
- rerankers;
- adapters;
- fine-tunes;
- small custom models.

For every training job preserve:

- exact code/container;
- dataset revision/checksums;
- base model/revision;
- preprocessing parameters;
- hyperparameters and random seeds where applicable;
- hardware/provider;
- checkpoints;
- validation metrics;
- estimated and actual spend;
- final artifact IDs and storage locations;
- reproducibility manifest.

## Artifact persistence

Cloud instances are disposable; useful outputs are not.

The broker must persist, according to project policy:

- LoRAs/adapters;
- model checkpoints;
- quantized exports;
- inference configs;
- training logs/metrics;
- validation samples/metrics;
- model cards/manifests;
- dataset manifests (not private raw data in Git);
- provenance and licenses.

Artifacts should be project-scoped and content-addressed/versioned where
practical.

## Routing economics

Route on **expected total cost of verified success**, not token price alone.

Compare:

- subscription capacity already paid for;
- pay-per-token/API inference;
- serverless GPU;
- temporary GPU pod;
- persistent endpoint;
- local compute when available in the future.

Include startup, model download/load, storage, retries, validation, idle time,
and expected failure rate.

## Observability / UI

Add a Model & Compute page showing:

- model registry and modality filters;
- newly discovered/recommended models;
- benchmark evidence and last verified date;
- active endpoints/GPUs/jobs;
- provider and model selected and why;
- estimated vs actual spend;
- current project/job budget;
- training progress and checkpoint list;
- model routing/refusal/failure telemetry;
- one-click stop/cancel;
- shadow-foreman comparisons;
- API-vs-GPU savings/overruns;
- credentials connection status without exposing secrets.

## Provider-neutral interfaces

Initial interface family:

```text
model.catalog.list
model.catalog.refresh
model.research.scan
model.benchmark.plan
model.benchmark.run
model.capability.get
model.route.plan
model.route.explain
model.foreman.shadow
model.refusal.record

compute.providers.list
compute.inventory.refresh
compute.quote
compute.provision
compute.status
compute.stop
compute.destroy
compute.cost.reconcile

secrets.provider.setup
secrets.provider.status
secrets.provider.delete

training.plan
training.quote
training.start
training.status
training.cancel
training.resume
training.artifacts

image.generate
image.edit

audio.transcribe
audio.synthesize
audio.convert
audio.diarize
audio.enhance
```

Adapters may expose additional capabilities; core orchestration depends on
capability contracts, not vendor names.

## Third-party routing, delegation, and GPU-efficiency evaluation track

**Priority: HIGH — operator directive 2026-09-30.**

Orchestrator should actively test mature third-party projects that can improve model
swapping, task delegation, RunPod/cloud use, inference throughput, context reuse,
and cost efficiency. These projects are implementation candidates and prior art,
not replacements for Orchestrator's provider-neutral control plane. Preserve the
existing workload contract, CAP/EVR evidence, budget gates, secret abstraction,
deterministic authorization boundaries, checkpointing, and measured-promotion
policy.

### Integration principle

Use two routing layers rather than collapsing everything into one gateway:

1. **Orchestrator semantic/capability routing** chooses task decomposition,
   capability class, quality floor, privacy constraints, context contract,
   model family/class, budget, verification, parallelism, and escalation policy.
2. **Provider/runtime routing** chooses the concrete endpoint/provider/replica,
   load-balancing path, cache-aware placement, retries/failover, and serving
   runtime.

External frameworks may implement or inform layer 2 and bounded parts of layer 1,
but they must not become the authority for spending, secrets, destructive writes,
or canonical Agent OS policy.

### Required prior-art candidates and disposition targets

The current agent must add/refresh prior-art registry entries and run bounded
spikes for these candidates. The dispositions below are starting hypotheses,
not automatic adoption decisions:

| Candidate | Initial disposition | What to test / subsume |
| --- | --- | --- |
| **SkyPilot** | WRAP / BORROW | Multi-cloud provisioning abstraction, RunPod lifecycle semantics, job recovery, spot/preemptible handling, resource selection, state persistence. Keep native provider adapters available for optimized fast paths. |
| **Native RunPod SDK/API** | WRAP | Provider-specific fast path for pods, serverless, inventory, lifecycle, health, pricing, and features SkyPilot cannot expose cleanly. |
| **TensorZero** | WRAP / EXPERIMENT | Unified model/provider gateway, experiment telemetry, feedback/evals, variants, retries/fallbacks, and A/B routing. Evaluate as an optional sidecar/telemetry plane feeding Agent OS CAP/EVR evidence rather than replacing the router. |
| **PydanticAI subagent patterns** | BORROW | Isolated child-agent context, per-tree usage accounting, delegation contracts, model-per-child selection, request/token/tool-call/cost limits. Prefer subsuming semantics into existing delegate machinery over adopting the framework wholesale. |
| **AgentScope** | BORROW / EXPERIMENT | Dynamic model-router middleware, leader/member team delegation, A2A/team topology, and task handoff patterns. Compare against current foreman + delegate DAG behavior. |
| **RouteLLM** | BORROW | Learned/calibrated strong-vs-weak routing and threshold selection. Do not promote learned routing until Agent OS has enough labeled task-family outcomes; use shadow/canary mode first. |
| **LiteLLM** | BORROW / OPTIONAL ISOLATED ADAPTER | Provider catalog, normalized API shapes, fallback/routing ideas, price metadata. Keep it outside the trusted core unless a pinned isolated deployment demonstrates enough benefit to justify dependency/supply-chain surface. |
| **vLLM** | WRAP | Baseline high-throughput self-hosted inference backend; continuous batching, prefix caching, quantization/runtime options, OpenAI-compatible serving. |
| **SGLang** | WRAP + HEAD-TO-HEAD BENCHMARK | Alternative high-performance inference runtime; benchmark continuous batching, prefix/radix caching, speculative decoding, chunked prefill, parallelism, quantization, and multi-LoRA against vLLM. |
| **LMCache** | WRAP / EXPERIMENT | Cross-request / cross-worker KV reuse and offload to CPU/SSD/shared stores. Test specifically on repeated Orchestrator/project prefixes and episodic worker rotation. |
| **AIBrix** | DEFER UNTIL MULTI-WORKER, THEN EXPERIMENT | Prefix-aware routing, model-aware autoscaling, LoRA density, and inference scheduling. Promote only when one-node/multi-replica or small-cluster scale makes scheduler overhead worthwhile. |
| **llm-d** | DEFER UNTIL MULTI-GPU CLUSTER | Cache/load-aware distributed scheduling, prefill/decode disaggregation, LoRA-aware routing, and cluster-scale inference. Treat as future large-cluster backend, not an immediate dependency. |

Also continuously search for newer maintained alternatives that cover the same
capability classes; these names are not architectural boundaries.

### Required benchmark dimensions

Every spike must be measured against the incumbent and recorded as EXP/EVR/DEC
evidence. At minimum measure, where applicable:

- total **cost per verified successful task**, not raw token/GPU price;
- accepted/validated work per GPU-dollar and per wall-clock hour;
- tokens/sec and requests/sec under representative concurrency;
- time-to-first-token and end-to-end latency;
- GPU utilization, VRAM occupancy, CPU/RAM/storage/network utilization, and paid
  idle time;
- startup/model-load/warmup time and warm-vs-cold economics;
- prefix/KV-cache hit rate, bytes reused, and recompute avoided;
- context/input-token savings from isolated subagents and cache reuse;
- task success, validator/test pass rate, review acceptance, retry/escalation
  rate, refusal/failure category, and attribution correctness;
- orchestration/framework overhead in latency, memory, CPU, dependency count,
  operational complexity, and failure modes;
- throughput and quality by exact model revision + quantization + serving engine
  + GPU + concurrency configuration;
- provider/API versus self-hosted break-even point;
- behavior under interruption, resume, retry, provider failure, and quota
  exhaustion.

Do not promote an integration merely because it improves one microbenchmark.
Prefer **cost per validated completion** and reliability on representative Agent
OS tasks.

### Concrete experiment sequence

Run the following in order unless measured evidence justifies reordering:

1. **Finish the already queued SkyPilot spike** with no launch/spend: map RunPod
   provision/status/stop/destroy/reconcile semantics, state ownership, secret
   bridging, recovery, and lifecycle gaps. Record WRAP vs in-house/native
   decision.
2. **Complete the fake-provider gated provisioning path** and write-ahead spend
   reservation before any new real paid-compute experiment.
3. **Build the runtime benchmark harness** keyed by
   `model@revision + quantization + engine + GPU + concurrency + cache mode`.
   Reuse throughput/CAP/EVR infrastructure.
4. **vLLM vs SGLang A/B** on the same served model/hardware/workload. Test
   concurrency, prefix reuse, quantization, chunked prefill/speculation where
   supported, and multi-LoRA where relevant.
5. **LMCache spike** on repeated Agent OS prefixes and episodic-agent workloads.
   Compare against native runtime prefix caching and no-cache baselines.
6. **PydanticAI-style isolated delegation experiment** using existing
   `orchestrate delegate`: child workers receive the smallest truthful Task
   Context Contract, separate history, explicit usage limits, and optionally a
   different model. Measure bootstrap/rediscovery cost versus context avoided.
7. **AgentScope pattern spike**: compare leader/member delegation and router
   middleware concepts against the incumbent foreman/DAG. Borrow only features
   with measurable value.
8. **TensorZero sidecar experiment**: mirror or route a bounded evaluation set
   through it, ingest cost/latency/variant/feedback telemetry into Agent OS
   evidence, and compare operational complexity with the native gateway.
9. **RouteLLM-style shadow router** once enough outcomes exist: learn or
   calibrate cheap->strong escalation thresholds per task family; no production
   authority until held-out EVRs show noninferior validation at lower expected
   cost.
10. **LiteLLM isolated comparison** only if provider-coverage gaps remain after
    the native gateway/TensorZero experiments. Pin versions, isolate credentials,
    and measure whether the coverage benefit exceeds dependency and operational
    risk.
11. **AIBrix experiment** once Orchestrator routinely runs multiple local/RunPod
    replicas, LoRAs, or model servers on one node/cluster and there is enough
    load for routing/autoscaling decisions to matter.
12. **llm-d experiment** only once a multi-GPU/multi-node workload exists that
    can meaningfully benefit from distributed cache/load-aware scheduling or
    prefill/decode disaggregation.

### GPU saturation / opportunistic backfill controller

Integrate these experiments with the existing GPU Saturation Controller roadmap.
When paid compute is already running, Orchestrator should measure whether spare
resources can safely execute useful checkpointable work without harming the
primary job.

Candidate backfill classes include:

- cheap local subagents for code search, documentation, static review, metadata
  extraction, test generation, and other automatically verifiable tasks;
- embeddings/reranking/index updates;
- queued evals and benchmark samples;
- LoRA/adaptor inference or training when memory/headroom permits;
- preprocessing and data transforms on otherwise idle CPU/RAM/storage/network.

Backfill must be preemptible, budget-accounted, sensitivity-aware, and subordinate
to the primary workload's latency/throughput SLA. Spawn more workers only when
measured expected value exceeds coordination, context, cache, and contention
cost.

### Promotion gates

A third-party runtime/framework may move from spike to supported adapter only
when:

1. representative tests show a material improvement in cost per verified
   successful task, utilization, reliability, latency, or developer throughput;
2. validation quality is noninferior to the incumbent on held-out tasks;
3. failures and attribution are observable and resumable;
4. secret handling and provider credentials remain behind Agent OS abstractions;
5. budget/spend/authorization gates remain authoritative outside the external
   component;
6. the integration can be disabled or replaced without corrupting canonical
   project/evidence state;
7. dependency and operational complexity are justified by measured benefit;
8. exact versions/configuration are recorded and reproducible;
9. rollback to the incumbent is tested.

Reject or defer candidates that add more coordination/runtime complexity than
their measured savings justify.

### New provider-neutral interfaces / evidence fields

Extend existing contracts only where evidence demonstrates a need. Candidate
interfaces/fields include:

```text
model.route.shadow
model.route.calibrate
model.route.variant_experiment
delegate.context_isolation
delegate.usage_budget

runtime.backends.list
runtime.benchmark
runtime.cache.status
runtime.cache.metrics
runtime.config.compare

compute.utilization
compute.backfill.plan
compute.backfill.start
compute.backfill.preempt

experiment.variant.record
experiment.feedback.record
```

Runtime evidence should be keyed by exact model revision and configuration,
including serving engine/version, quantization, GPU SKU/count, tensor/pipeline
parallelism, concurrency, cache backend/mode, LoRA/adaptor set, and important
runtime flags. Do not generalize one benchmark across materially different
configurations.


## Implementation order

### Phase 0 — design/eval foundation (no paid compute)
- Prior-art lookup per Orchestrator policy.
- Define workload, model-capability, compute-quote, secret-reference, and
  artifact schemas.
- Extend capability evidence to modality + deployment + exact model revision.
- Add fake/synthetic provider for deterministic tests.
- Add shadow-foreman evaluation contract.
- Add refusal/failure telemetry taxonomy.

### Phase 1 — generic gateway + credentials
- Generic OpenAI-compatible inference adapter for external/self-hosted text/code.
- OS keyring/environment secret abstraction.
- Provider status/setup commands.
- No provider-specific scheduler branches.

### Phase 2 — RunPod first adapter
- Read-only inventory/pricing/quote first.
- Pod/serverless lifecycle after tests.
- Auto shutdown and cost reconciliation.
- No autonomous material spend until budget policy is configured.

### Phase 3 — intelligent model routing
- Continuous model catalog/research refresh.
- API-vs-GPU break-even logic.
- Foreman shadow mode.
- Measured CAP evidence feeds routing.
- Promote automatic route/model swaps only after eval gates.

### Phase 4 — image + ML training
- Image inference adapters.
- Training planner/quote engine.
- LoRA/adaptation pipeline.
- Checkpoint/artifact persistence.
- Resume/preemption handling.

### Phase 5 — voice/audio
- ASR/TTS/audio capability registry + adapters.
- Audio preprocessing/planning.
- Voice/audio training/adaptation quotes and workflows.
- Streaming/latency metrics where applicable.

### Phase 6 — continual optimization
- Scheduled Research Radar refresh.
- Benchmark material new releases against representative Agent OS workloads.
- Re-price providers.
- Flag beneficial swaps; canary/shadow before automatic promotion.

## Acceptance criteria

The first complete implementation should satisfy all of these:

1. A new text/code model can be added through registry + adapter configuration
   without scheduler edits.
2. A new image or audio model can be represented without changing the core
   workload schema.
3. Orchestrator can compare at least API vs RunPod compute for one real model
   and produce a no-spend quote.
4. Credentials can be configured locally without appearing in Git/logs.
5. A hard job budget cannot be exceeded silently.
6. Idle cloud compute is automatically stopped.
7. A model training request can produce a low/expected/high quote before launch.
8. LoRA/adaptation jobs retain reproducible manifests and resumable checkpoints.
9. Voice/audio workloads have explicit ASR/TTS/conversion/diarization capability
   representation and training-planning support.
10. The abliterated foreman can run in shadow mode and its routes are compared
    against incumbent results/costs/refusals.
11. Model Research Radar can discover a new release, record provenance/license/
    hardware/pricing metadata, and queue an eval without rewriting core code.
12. Subscription models remain eligible for benign work; open/abliterated
    models remain eligible where measured capability, privacy, or low-refusal
    behavior makes them the better route.
13. Paid provisioning, budget increases, consequential writes, and secret
    access remain under deterministic policy/approval controls.

## Immediate handoff to the current Orchestrator development agent

This is a new explicit operator instruction and supersedes the prior
"maintenance/no speculative subsystem" next action.

Start with Phase 0 and the no-cost/read-only parts of Phases 1–2. Reuse the
existing router, provider registry, CAP evidence, evaluation harness, policy
gates, telemetry, continuation checkpoints, and research-radar primitives.
Do not create parallel duplicates.

Before adding a new dependency or subsystem, run the required prior-art lookup.
Leave the first paid RunPod provision/train action behind an approval/budget
gate; implementation and quote/inventory calls may proceed without spending.

Finish the slice with tests, updated implementation/status evidence, and a new
Orchestrator checkpoint so the next agent can continue without this
conversation.
