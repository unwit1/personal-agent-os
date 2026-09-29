# Model infrastructure: plugging in open-weight and abliterated models

Status: IMP-0015 Phase 0/1 slice (2026-09-29). Roadmap:
`projects/personal-agent-os/roadmap/model-infrastructure-manager.md`.

This page covers what works today: registering any OpenAI-compatible endpoint
(including a local or cloud-hosted abliterated model), routing work to it by
provider-neutral workload requirements, giving it a neutral Task Context
Contract, keeping its credentials out of Git, and measuring its refusals.
Cloud GPU provisioning, quotes, training and image/audio adapters are later
phases; paid compute stays behind the budget/approval gate.

## 1. Serve the model

Any server that speaks the OpenAI Chat Completions API works: vLLM
(`vllm serve <model> --port 8000`), Ollama (`http://127.0.0.1:11434`), LM
Studio, llama.cpp `llama-server`, TGI, or a proxy in front of a RunPod pod or
serverless endpoint. Agent OS posts to `<base_url>/v1/chat/completions`.

## 2. Store its key (only if the endpoint needs one)

```powershell
agent-os orchestrate secrets set secrets://local-abliterated/default   # hidden prompt -> OS keyring
agent-os orchestrate secrets status secrets://local-abliterated/default
```

The environment variable `AGENT_OS_SECRET_LOCAL_ABLITERATED_DEFAULT` works
instead of the keyring (CI, containers). The registry stores only the
reference. `status` reports presence and source, never the value. An entry
with a `secret_ref` never falls back to a vendor key such as `OPENAI_API_KEY`,
so a self-hosted endpoint cannot receive a cloud credential by accident.

## 3. Register it

```powershell
agent-os orchestrate model-add --id local-abliterated `
    --base-url http://127.0.0.1:8000 --model <exact-model-id> `
    --refusal-profile abliterated --classes fast,balanced `
    --license apache-2.0 --context-window 131072          # preview only
# ...review the entry, then add --write
```

This writes one entry to the machine-local registry
(`~/.agent-os/providers.json`, never Git):

```json
{"id": "local-abliterated", "adapter": "openai_api", "roles": ["inline"],
 "models": {"fast": "<model>", "balanced": "<model>"}, "costs": {"fast": 0.25, "balanced": 0.25},
 "options": {"base_url": "http://127.0.0.1:8000", "send_reasoning_effort": false},
 "profile": {"deployment": "local", "modalities": ["text", "code"], "open_weights": true,
             "license": "apache-2.0", "refusal_profile": "abliterated", "context_window": 131072}}
```

- `roles: ["inline"]`: HTTP workers have no repository tools, so they serve
  self-contained prompts (delegate `--role inline`, rendered context
  contracts). The coding roles keep using the CLI workers until measured
  evidence justifies more.
- `deployment` defaults to `local` for a loopback URL and `api` otherwise. Pass
  `--deployment gpu_pod` or `serverless` for cloud-hosted weights.
- `probe` checks configuration only (URL and key present), not that the server
  is running. A dead server fails the call as `unavailable`, which feeds the
  breaker (DEC-0029).
- `refusal_profile` describes behaviour; it is not a quality score. Measured
  CAP evidence still decides competence (`agent-os orchestrate capability`).

## 4. Route to it

Workloads state requirements against profiles, not vendor names:

```powershell
# must stay on local/self-hosted weights (e.g. private data)
agent-os orchestrate delegate --role inline --require deployment=local,gpu_pod ...
# prefer a low-refusal model when one is usable, otherwise normal routing
agent-os orchestrate delegate --role inline --prefer refusal_profile=abliterated,low ...
```

Orchestrated tasks take the same object in `tasks.json`:
`"requirements": {"deployment": ["local"], "prefer_refusal_profile": ["abliterated"]}`.

| Key | Kind | Values |
|---|---|---|
| `deployment` | hard | subscription, api, serverless, gpu_pod, local |
| `refusal_profile` | hard | standard, low, abliterated, unknown |
| `modalities` | hard (all listed) | text, code, vision, image, audio, multimodal, embedding |
| `open_weights` | hard | true/false |
| `prefer_deployment`, `prefer_refusal_profile` | soft | as above |

Hard keys filter providers. Soft keys order usable candidates ahead of cost,
so if no preferred model is usable, routing proceeds normally. Requirements
also bind overrides: an override cannot send a `deployment=local` workload to
a remote provider. Reviewers and repairers inherit their subject's
requirements. Unknown keys or values are rejected, so a typo cannot silently
widen routing. Every selection records the chosen `profile`.

## 5. Give it a neutral context

`context_contract.build(...)` + `render(...)` produce the same prompt text for
every provider: objective, facts, constraints, inputs fenced as untrusted data,
and the output shape. There is no vendor persona and nothing provider-specific.
The same contract is therefore a fair comparison across models.

Minimization is required and laundering is not (roadmap invariant 4):
- a fact marked `safety_relevant` can never be dropped
  (`ContextLaunderingError`);
- every omitted fact or input is listed in `contract["omitted"]`;
- a stable preamble can be sent as the endpoint's system turn with the
  `options.system` registry field.

## 6. Watch refusals

When a completed answer misses its contract, delegate classifies why
(`provider_policy`, `unsupported_capability`, `ambiguous_request`,
`authorization`, `worker_failure`) and appends to
`<orchestrator home>/refusals.jsonl`. `agent-os orchestrate refusals`
aggregates the file by provider, model and refusal profile. This is the
evidence the roadmap's shadow foreman and routing promotion will use.

## 7. Evaluate it as a foreman (shadow mode)

```powershell
agent-os orchestrate foreman-shadow propose <run> --prefer refusal_profile=abliterated   # one real call
agent-os orchestrate foreman-shadow compare <run>                                          # deterministic
agent-os orchestrate foreman-shadow report
```

`propose` renders the run's goal and planned tasks as a Task Context Contract
(including the safety-relevant fact that this is a shadow evaluation) and asks
the foreman model for a DAG with a capability class per task. The proposal is
stored under `<orchestrator home>/foreman-shadow/<run>/`. `compare` scores each
task against what actually happened:
- `agree`: same class as the incumbent;
- `cheaper_likely_ok`: a cheaper class, and the incumbent passed on the first
  attempt with no retries or escalation (a potential saving);
- `cheaper_risky`: a cheaper class, but the incumbent needed retries or
  escalation;
- `stronger`: a more expensive class than needed.

It also lists DAG edge differences, task coverage and any foreman refusal.
The foreman gets no routing authority from this; promotion needs eval and
shadow evidence (roadmap Phase 3).

## 8. Describe workloads and quote them before spending

A workload (`workload.py`, schema `personal-agent/workload/v1`) states type
(inference, batch, embedding, training, fine_tune, adapter_training,
evaluation, conversion, serving), modalities (text, code, vision, image,
audio, ...), capabilities (e.g. `asr`, `diarization`, `image_editing`,
`lora`), sizes (tokens, items, images, audio seconds, dataset tokens,
epochs), resources, sensitivity, budget and reliability. New modalities need
no schema change.

Sensitivity sets a deployment floor, and explicit requirements can only
narrow it:
- `secret`: local only;
- `private`: local, GPU pod or serverless (self-hosted weights);
- `internal` and `public`: no constraint.

```powershell
agent-os orchestrate quote --workload job.json --options options.json
```

`options.json` lists priced candidates:
- `{"kind": "api", "price_in_per_mtok": .., "price_out_per_mtok": ..}`;
- `{"kind": "gpu_pod" | "serverless", "gpu_hourly_usd": .., "gen_tokens_per_second": .., "train_tokens_per_second": .., "startup_minutes": ..}`.

The quote ranks options by the expected cost of a verified success, with
low/expected/high bands. The estimate includes startup, idle tail, storage
and expected retries, plus the API-vs-GPU saving. Each option carries a
**budget gate**. A paid option is `allowed` only when the workload budget is
`approved: true` *and* the high estimate fits `job_hard_cap_usd` (and
`project_usd`). Otherwise the gate says `requires_approval` and why. A quote
never provisions or spends anything.

Artifact manifests (`artifacts.py`) record models, adapters, checkpoints and
outputs by URI, sha256, base model and revision, and a training-config
digest. `verify` checks a local checkpoint before resume, and
`latest_resumable` picks the newest checkpoint of a job.

## What stays gated

The model you pick never becomes the authorization boundary. Consequential
writes, pushes/publication (DEC-0022), spending, budget changes and secret
access stay deterministic policy gates, whichever provider or refusal
profile serves a task.
