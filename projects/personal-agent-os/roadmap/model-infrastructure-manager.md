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
