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

## 0. Credentials (one-time, pop-up dialogs)

```powershell
agent-os orchestrate secrets setup        # masked pop-ups -> Windows Credential Manager; blank/Cancel skips
agent-os orchestrate secrets status       # presence and source only, never values
```

| Reference | What it unlocks | Where to get it | Needed now? |
|---|---|---|---|
| `secrets://runpod/default` | authenticated RunPod inventory; pod provisioning later, after budget approval | RunPod console > Settings > API Keys (read-only is enough until provisioning is approved) | optional (public prices work without it) |
| `secrets://huggingface/default` | Research Radar rate limits and gated-repo metadata | huggingface.co > Settings > Access Tokens, type Read | optional |
| `secrets://local-abliterated/default` | your model server's key, if it requires one (e.g. vLLM `--api-key`) | the key you set on the server | only if your server needs a key |

No payment details go into Agent OS. Fund RunPod in its own console, with
its spending controls.

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

The operator budget is machine-wide (`~/.agent-os/budget.json`, outside Git):

```powershell
agent-os orchestrate budget show
agent-os orchestrate budget set --project-usd 10 --job-cap-usd 5 --note "why"   # operator only; every change is kept in budget-history.jsonl
```

Quotes gate on it: a paid option needs its high estimate at or under the
per-job cap and the remaining project budget (after recorded spend). A
workload's own `budget` block can only tighten those limits.

Live GPU prices come from the read-only Compute Broker:

```powershell
agent-os orchestrate compute inventory --min-vram 80          # RunPod gpuTypes, secure + community tiers
agent-os orchestrate quote --workload job.json --options api.json --gpu-from runpod --gen-tps 1500
```

A RunPod key is optional (`secrets://runpod/default`) and sent only when
configured. Throughput must be given, measured for the model and serving
engine (e.g. a vLLM benchmark); the broker never invents it. EVR-0017 is the
first live example: a private batch of 20k items came out at about $5 on an
A100 community pod versus about $379 at an example API price, under
explicitly assumed throughput. It is blocked by the budget gate until
approved.

Replace assumed throughput with measurements once a model is served:

```powershell
agent-os orchestrate throughput measure --provider local-abliterated --gpu "A100 PCIe" --engine vllm-0.30 --concurrency 8 --requests 32
agent-os orchestrate quote --workload job.json --options api.json --gpu-from runpod --model <model-id>
```

`measure` sends N concurrent requests to your own endpoint and records the
aggregate completion tokens/s from the server's reported usage. With
`--model` and no `--gen-tps`, quotes price only the GPUs that have recorded
throughput. Measured evidence wins over benchmark or assumed numbers.

Artifact manifests (`artifacts.py`) record models, adapters, checkpoints and
outputs by URI, sha256, base model and revision, and a training-config
digest. `verify` checks a local checkpoint before resume, and
`latest_resumable` picks the newest checkpoint of a job.

## 9. Discover new models (Research Radar)

```powershell
agent-os orchestrate radar scan                                   # default scans: trending text, abliterated, VLM, image, ASR, TTS
agent-os orchestrate radar scan --search "coder" --pipeline text-generation --sort downloads
agent-os orchestrate radar catalog --refusal-profile abliterated
agent-os orchestrate radar catalog --modality audio
```

Each scan merges into `<orchestrator home>/model-catalog.json` (local, not
Git). A catalog entry records the exact repo and revision sha, pipeline,
modalities and capabilities, license, base model, quantization tags,
parameter count (when the repo has safetensors), downloads, and a
*declared* refusal hint (`abliterated`/`uncensored` tags). It reports models
and revisions it hasn't seen before. Those with a known license and at least
`--min-downloads` (default 10,000) are appended to `eval-queue.jsonl` with
suggested suites. Nothing downloads weights. Public benchmark claims are not
evidence; measured Agent OS evals decide routing.

To try a catalog model:
1. quote the pod with `orchestrate quote --gpu-from runpod`;
2. serve the model at the catalog's `revision` (e.g. vLLM on the pod);
3. register it with `orchestrate model-add`, passing the catalog's
   `--license` and `--refusal-profile`.

## 10. Evaluate a served catalog model

```powershell
agent-os orchestrate model-add --id local-x --base-url http://<pod>:8000 --model <catalog model_id> --revision <catalog sha> --roles inline,analyst --write
agent-os orchestrate eval-queue plan --model <catalog model_id>        # readiness, candidate and incumbent routes
agent-os orchestrate eval-queue run  --model <catalog model_id> --max-calls 6
```

Add `--revision <catalog sha>` to `model-add` so capability evidence is
keyed by the exact revision served (`model@<sha12>`). A re-quantized or
updated checkpoint then starts with its own evidence.

`run` compares the served model against an established incumbent on each
suggested suite through `orchestrate eval`. That writes an EVR and records
CAP evidence, and the queue records `evaluated`, `invalid` or `error`.
Register the endpoint with the `analyst` role: without it the router would
answer eval cases with a different provider. The runner refuses such
candidates and marks any run answered by another provider invalid
(FND-0014).

## 11. See it all in the GUI

`agent-os orchestrate gui` → Simple Mode → **Models & compute** shows the
following, read-only:
- registered models with deployment, refusal profile and roles;
- the discovered catalog, including abliterated hints;
- cached GPU prices and measured throughput;
- the eval queue;
- refusal and shadow-foreman summaries.

Opening it makes no network or model call. Refresh prices with
`orchestrate compute inventory`.

## 12. Deploy a session foreman from a Hugging Face link

GUI → Simple Mode → **Session foreman**: set the project budget and the budget
for this job, paste a Hugging Face model link, press **Check Cost** (no
spend), then **Deploy as Foreman**. CLI equivalent:

```powershell
agent-os orchestrate foreman preview https://huggingface.co/Qwen/Qwen2.5-14B-Instruct --job-usd 1.5
agent-os orchestrate foreman deploy  https://huggingface.co/Qwen/Qwen2.5-14B-Instruct --job-usd 1.5   # foreground; returns after teardown
agent-os orchestrate foreman status | stop
agent-os orchestrate foreman eval                       # judgement + efficiency eval of the live foreman (real calls)
```

What happens (`foreman_deploy.py`), with no further input:

1. The model's exact revision, size, dtypes, gating and `config.json`
   (context length, KV-cache shape) are read from Hugging Face. The GPU memory
   need is estimated from them. GGUF-only repositories are refused, and so are
   gated repositories your token cannot read.
2. Every RunPod offer that fits the memory need (1/2/4/8 GPUs; the tensor-parallel
   count must divide the attention heads) and leaves at least 30 minutes of
   runtime inside the job budget is grouped by GPU count and cloud tier. One pod
   request per group lists all of that group's GPU types, cheapest first
   (`gpuTypePriority: custom`). A sold-out group falls through to the next.
3. The pod runs `vllm/vllm-openai` pinned to the revision, guarded by a fresh
   API key in the keyring (`secrets://foreman/endpoint`). The Hugging Face
   token is sent only for a gated or private repository.
4. Once `/v1/models` serves the model, it is registered as
   `foreman-<name>` (`roles: planner, inline`). **Every run created while it is
   live uses it as its planner.** A run created while the model is still loading
   shows PLANNING (not BLOCKED) and waits. If the deployment fails or ends, the
   run falls back to its normal planner. A planner override you set yourself
   takes precedence.
5. The foreman decides which model runs each task through the
   `capability_class`/`effort` it gives each task. Its plans go through the
   same `planner.expand` checks as any planner. It never runs coding roles.
6. A watchdog writes the pod's cost to the spend ledger every 30 s. It deletes the
   pod before the next tick could cross 95% of the job budget, or when the
   remaining project budget runs out. It also deletes it once every attached run
   has planned and the foreman has been idle for the chosen number of minutes,
   and when you press Stop. The provider entry is removed at teardown.

Limitation: the watchdog lives in the GUI (or `foreman deploy`) process. If
that process is not running, the pod keeps billing until the GUI next starts.
On startup the GUI deletes it at once if its deadline has passed, and deletes
any orphan pod left by a crash during creation. Stop it from the RunPod console
if you will be away.

`foreman eval` sends the foreman the planner prompt the engine uses, for 7
labelled goals (typo → `fast`, … concurrency and security design → at least one
`reasoning` task). It scores: plan validity, over-provisioned tasks (wasted spend),
under-provisioned cases (a needed `reasoning` task missing), task count, the plan's
routing cost relative to the cheapest plan the labels allow, tokens, latency and
GPU dollars. Reports go to `<orchestrator home>/foreman-eval/`.

## Gated provisioning interface (slice 2)

Contract pinned by DEC-0042 (IMP-0015 slice 2). Slice 2 implements and tests
it against a **fake provider only**: no real adapter is called, there is no
network, and nothing is spent. The design borrows SkyPilot (PA-skypilot): its
cluster status set, its cluster name used as the idempotency key, and its
provider-side autostop. The difference here is that autostop comes from the
budget, not from idle time.

### Modules and functions

`src/agent_os/orchestrator/provision.py`. Every function returns the job
record (a JSON-able dict) as persisted:

```python
provision(request, *, provider=None, home=None, budget_home=None, clock=None)
status(job_id, *, provider=None, home=None, budget_home=None, clock=None)
stop(job_id, *, provider=None, home=None, budget_home=None, clock=None)
destroy(job_id, *, provider=None, home=None, budget_home=None, clock=None)
reconcile(job_id, actual_usd=None, *, provider=None, home=None, budget_home=None, clock=None)
```

Parameters:
- `home` overrides `orchestrator_home()`.
- `budget_home` is passed to `budget.py`, so tests use temporary directories
  for both.
- `clock` is a callable that returns epoch seconds (default `time.time`).
  History timestamps are ISO-8601 UTC strings derived from it.
- An unknown `job_id` raises `KeyError`.

`src/agent_os/orchestrator/compute_fake.py` holds the provider protocol and
`FakeProvider`:

| Method | Returns |
| --- | --- |
| `launch(spec)` | `{"instance_id"}` |
| `poll(instance_id)` | `{"state", "runtime_seconds", "cost_usd"}`, where `state` is `running`, `stopped` or `terminated` |
| `stop(instance_id)` | — |
| `terminate(instance_id)` | — |

`spec` carries `name` (= `job_id`), `gpu`, `hourly_usd`,
`max_runtime_seconds` and `secret_ref`. `launch` is idempotent by
`spec["name"]`: a second launch with the same name returns the same
`instance_id`, as SkyPilot's `sky launch -c <name>` does. That makes resuming
a crashed `launching` step safe.

`FakeProvider(clock=None, state_path=None)` works as follows:
- It is in-memory and never touches the network.
- Cost is `runtime_seconds / 3600 * hourly_usd`.
- It enforces `max_runtime_seconds` itself, so it models provider-side
  autostop. A poll after the deadline reports `stopped`, with runtime capped
  at the deadline.
- `state_path` is optional, used only by the CLI/MCP so that a fake job
  survives across processes (`<home>/compute-jobs/fake-provider.json`).
  Tests stay purely in memory.

### Provider resolution

With `provider=None`, a request whose `provider` is `fake` uses
`FakeProvider`. **Any other provider name ends in `blocked`**: slice 2 wires
no real adapter, and a real launch needs a write-enabled key plus operator
confirmation (slice 3). Nothing is reserved or launched.

### Request validation

Validation errors raise `ValueError` and persist nothing:
- `provider` and `gpu` are required strings.
- `hourly_usd` must be greater than 0.
- `estimate` must be `{low, expected, high}`, numeric, with
  `0 <= low <= expected <= high` and `high > 0`.
- `max_runtime_seconds` is optional and must be greater than 0.
- `budget` is optional: a workload budget block, which can only tighten.
- `job_id` is optional and must match `^[a-z0-9][a-z0-9-]{2,63}$`. When it is
  absent it is `cj-` + the first 12 hex digits of the sha256 of the canonical
  (sorted-key) request JSON, so the same request names the same job.
- `secret_ref` is optional and must be a `secrets://<provider>/<name>`
  reference. Any other credential-looking key (`api_key`, `token`,
  `password`, `secret`, ...) or a raw value is rejected before anything
  reaches disk. The reference is stored, never resolved, in slice 2.

### Job record

The record lives at `<orchestrator_home()>/compute-jobs/<job_id>.json` and is
always written with `storage.write_json` (atomic). Fields:
- `job_id`, `provider`, `gpu`, `hourly_usd`;
- `estimate {low, expected, high}`, `reservation_usd`;
- `max_runtime_seconds`, `auto_stop_at` (ISO, set at launch);
- `instance_id`, `state`;
- `runtime_seconds` and `cost_usd` (last poll), `reason` (for
  `blocked`/`failed`), `reconcile` (after reconcile);
- `history[]` of `{at, from, to, reason}`;
- `secret_ref`.

### Lifecycle

```
requested -> reserved -> launching -> running -> stopping -> stopped -> destroyed -> reconciled
requested -> blocked                                  (precondition failed; terminal)
requested|reserved|launching|running|stopping|stopped -> failed
failed -> destroyed | reconciled
```

Every transition goes through one `transition(record, to, reason)` helper,
which checks this table and appends to `history`. A transition that is not
listed raises `ValueError`. `blocked` and `reconciled` are terminal.

### Preconditions (budget gate)

`gate = budget.effective(request.get("budget"), budget_home)`. Provisioning
continues only if all of these hold:
- `gate["approved"]` is true;
- `job_hard_cap_usd` and `project_usd` are both set;
- `estimate.high <= job_hard_cap_usd`;
- `estimate.high <= project_usd`;
- `max_runtime_seconds` (see Mandatory auto-stop), computed here from
  `estimate.high`, is greater than 0.

Otherwise the job goes `requested -> blocked` with the failing check as
`reason`. Nothing is reserved or launched. Every check, including the
runtime one, runs before the ledger reservation is written, so a job never
needs a `reserved -> blocked` transition.

### Write-ahead reservation

The pattern follows IMP-0013 / DEC-0020:
1. Persist `requested`.
2. Append the ledger entry
   `budget.record_spend(estimate.high, job_id=…, kind="reserved")`.
3. Persist `reserved` with `reservation_usd = estimate.high`.
4. Persist `launching` **before** calling `provider.launch`.
5. Persist `instance_id`, `auto_stop_at` and `running` after the launch
   returns.

If `launch` raises, the job goes to `failed` with the error as `reason`.

Ledger appends are idempotent per `(job_id, kind)`: the ledger is scanned
before appending. When the ledger already holds this job's reservation, the
gate has already passed, so a resume goes straight to `reserved` instead of
counting its own reservation against itself.

### Mandatory auto-stop

```
max_runtime_seconds = floor(min(request.max_runtime_seconds or inf, estimate.high / hourly_usd * 3600))
```

It is computed from `estimate.high` during the precondition check, before
the ledger reservation is written; the reservation that follows has the same
amount (`reservation_usd = estimate.high`). Because
`estimate.high <= min(job cap, remaining project)`, billed runtime can never
exceed what the budget cap allows. If the value is `<= 0`, the job goes
`requested -> blocked` and nothing is reserved.

The deadline is enforced in two places:
- The provider receives the limit in `spec`. Its own stop is what survives
  Agent OS dying; this is the gap the foreman watchdog has.
- `status()` checks `clock() >= auto_stop_at` and stops the job itself.

Either way the history records `running -> stopping -> stopped` with reason
`auto_stop`.

### Operations

- **`provision`** is idempotent and resumable:
  - an existing job in `requested`, `reserved` or `launching` continues from
    that state;
  - any other state is returned unchanged.
- **`status`** polls the provider when an `instance_id` exists, updates
  `runtime_seconds`/`cost_usd`, applies auto-stop and follows provider-side
  `stopped`/`terminated`. Because auto-stop calls `provider.stop` and writes
  the record, `status` is **not** read-only (MCP `readOnlyHint: false`); it
  never terminates or deletes anything.
- **`stop`** goes `running -> stopping -> stopped` via `provider.stop`. It is
  a no-op once the job is stopped or later.
- **`destroy`** stops first when the job is running, then
  `provider.terminate`, then `destroyed`. It is a no-op once the job is
  destroyed or reconciled.
- **`reconcile`** runs from `destroyed` or `failed`; a `failed` job with a
  known instance is terminated and destroyed first. Steps:
  1. `actual_usd` defaults to the last polled `cost_usd` (0 if none was
     launched).
  2. Append `kind="actual"` for `actual_usd` and `kind="release"` for the
     amount of this `job_id`'s `kind="reserved"` ledger entry (both
     idempotent per `(job_id, kind)`). The release amount comes from the
     ledger scan already done for idempotency, **not** from
     `record.reservation_usd`: a job that failed after the ledger
     reservation was written but before `reserved` was persisted still
     releases its full reservation, so no orphan reservation lowers
     `budget.remaining()`. With no `reserved` entry, nothing is released.
  3. Store `reconcile {actual_usd, estimate_expected, variance_usd,
     within_band, over_reservation}` and move to `reconciled`.

  Net ledger effect: only actual spend remains. Reconciling a job that is
  already reconciled returns it unchanged.

### CLI and MCP

The CLI extends the existing `orchestrate compute` subcommand:

```powershell
agent-os orchestrate compute provision --request job.json   # JSON request as above
agent-os orchestrate compute status    <job_id>
agent-os orchestrate compute stop      <job_id>
agent-os orchestrate compute destroy   <job_id>
agent-os orchestrate compute reconcile <job_id> [--actual-usd 0.42]
```

MCP tools follow the `namespace.action` pattern in `mcp_server.py`:

| Tool | Arguments | Annotations |
| --- | --- | --- |
| `compute.provision` | `request` | `destructiveHint: false` |
| `compute.status` | `job_id` | `readOnlyHint: false`, `destructiveHint: false` (may auto-stop) |
| `compute.stop` | `job_id` | `destructiveHint: true` |
| `compute.destroy` | `job_id` | `destructiveHint: true` |
| `compute.reconcile` | `job_id`, optional `actual_usd` | — |

All of them carry `openWorldHint: false`. Both surfaces use
`FakeProvider(state_path=…)`. Gate and validation outcomes come back as data
(`blocked` plus `reason`) or as an error message, never as a traceback.

### Tests

`tests/test_provision.py`, all with temporary homes and an injected clock:
- an unapproved budget, high above the cap, and high above the project
  budget each give `blocked`, with no ledger entry and no launch;
- the happy path: the ledger shows reserved, then actual + release, and
  `budget.spent()` equals the actual cost;
- advancing the clock past `auto_stop_at` gives `stopped` with reason
  `auto_stop`;
- `provision` twice gives one reservation and one launch;
- resume after a simulated crash at `reserved` and at `launching`;
- an illegal transition raises `ValueError`;
- a raw secret raises `ValueError` and leaves no file;
- a non-fake provider gives `blocked`;
- `reconcile` is idempotent.

## What stays gated

The model you pick never becomes the authorization boundary. Consequential
writes, pushes/publication (DEC-0022), spending, budget changes and secret
access stay deterministic policy gates, whichever provider or refusal
profile serves a task.

## 13. Paid outside credits: off by default, per run

GUI: **Allow paid outside credits for this run (OpenRouter / RunPod)**, next to
Continue Roadmap and Start This Task. The checkbox is remembered per browser.
The run policy key is `allow_paid_spend` (default `false`).

- **Off:** the run routes only to your subscriptions (Claude Code, Codex) and
  local models. Providers with deployment `api`, `gpu_pod` or `serverless`
  (OpenRouter, API-key workers, rented pods and their coding agents) are
  excluded, even when they are cheaper. A paid session foreman (OpenRouter or
  Hugging Face) hands planning to its subscription backup. If it has no backup,
  the normal planner is used; the reason is recorded in the run.
- **On:** paid routes compete on cost like any other provider, so the cheapest
  route that fits wins.

This switch only controls routing. Renting a GPU is still its own operator
action (Deploy as Foreman), gated by the job budget.
