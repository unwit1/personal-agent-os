# Model infrastructure: plugging in open-weight and abliterated models

Status: IMP-0015 Phase 0/1 slice (2026-09-29) + IMP-0015 ASAP slice FreeComputeBroker (2026-10-01). Roadmap:
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

Contract pinned by DEC-0043 (IMP-0015 slice 2). Slice 2 implements and tests
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
| `lookup(name)` | `instance_id` of the instance created under `name`, or `None` |
| `poll(instance_id)` | `{"state", "runtime_seconds", "cost_usd"}`, where `state` is `running`, `stopped` or `terminated` |
| `stop(instance_id)` | — |
| `terminate(instance_id)` | — |

`spec` carries `name` (= `job_id`), `gpu`, `hourly_usd`,
`max_runtime_seconds` and `secret_ref`. `launch` is idempotent by
`spec["name"]`: a second launch with the same name returns the same
`instance_id`, as SkyPilot's `sky launch -c <name>` does. It is
launch-or-lookup: an instance the provider created under that name is found,
even if the call that created it raised before returning. That makes resuming
a crashed or failed `launching` step safe, and it is the only way Agent OS
finds an instance whose id it never received. Slice 3 adapters must keep this
lookup-first behavior.

`provision()` calls `lookup(job_id)` first when the provider has it, and
launches only when that returns `None`. Adapters must offer `lookup` or keep
`launch` idempotent by name.

`FakeProvider(hourly_usd=1.0, clock=None, fail_launch=False, state_path=None)`
works as follows:
- It never touches the network.
- Cost is `runtime_seconds / 3600 * hourly_usd`, using each instance's own
  `hourly_usd` taken from its `spec` (the constructor value is only the
  default), so one shared provider prices every instance correctly.
- It enforces `max_runtime_seconds` itself, so it models provider-side
  autostop. A poll after the deadline reports `stopped`, with runtime capped
  at the deadline.
- `state_path` is optional. Whenever `provision` resolves provider `fake`
  with `provider=None` (CLI, MCP, and library), state persists at
  `<home>/compute-providers/fake.json`, so a fake job survives new processes.
  Without `state_path` it is purely in memory.
- It has a test-only fault hook, `fail_launch`: `launch` creates the
  instance, persists it, then raises, which models a provider that creates an
  instance but loses the response. A later `launch` with the same name
  returns that instance.

The CLI and MCP resolve `budget_home` the standard way: next to the provider
registry, with the `AGENT_OS_PROVIDERS` override. There is no
`AGENT_OS_BUDGET_HOME` variable.

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
requested -> blocked                                  (precondition failed)
blocked -> requested                                  (only from provision(): retry)
requested|reserved|launching|running|stopping|stopped -> failed
failed -> destroyed | reconciled
```

Every transition goes through one `transition(record, to, reason)` helper,
which checks this table and appends to `history`. A transition that is not
listed raises `ValueError`. `reconciled` is terminal. `blocked` is at rest
(nothing reserved, nothing launched): `status`, `stop`, `destroy` and
`reconcile` return it unchanged, and only `provision` leaves it (see
Operations).

`launching -> failed` is allowed only once `instance_id` is known. A
`launching` job never fails without it, because its instance may exist at the
provider (see Write-ahead reservation).

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

If `launch` raises, the provider may already have created the instance. So
the job **stays in `launching`**, with the error stored as `reason` and
`launch_attempts` incremented, and the ledger reservation stays held. There is
no `failed` transition and no release. Recovery always goes through the
idempotent launch-or-lookup on `spec["name"]`:
- `provision` again resumes `launching` and calls `launch(spec)`. It gets the
  existing instance (or a new one) and moves to `running`, and there is still
  one instance and one reservation.
- `destroy` on a `launching` job abandons it: it calls `launch(spec)` to learn
  the `instance_id` and persists it, moves `launching -> failed` (reason
  `abandoned_launch`), calls `provider.terminate`, then moves
  `failed -> destroyed`. Only then can `reconcile` release the reservation,
  using the polled cost as `actual_usd`.
- If that lookup raises again, `destroy` raises, and the job stays in
  `launching` with the reservation held. A held reservation of at most
  `estimate.high` is the safe failure mode. An untracked instance with a
  released reservation is not.

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
  - an existing job in `blocked` is re-evaluated. It moves
    `blocked -> requested` (reason `retry`, recorded in `history`), and the
    full precondition check runs again against the current
    `budget.effective`. A job that is still blocked goes back to `blocked`
    with the new reason. A job that now passes reserves and launches as
    usual. The default idempotency key therefore stays usable after an
    operator approves or raises the budget, with no need to change the
    request or invent a `job_id`;
  - any other state is returned unchanged.
- **`status`** polls the provider when an `instance_id` exists, updates
  `runtime_seconds`/`cost_usd`, applies auto-stop and follows provider-side
  `stopped`/`terminated`. Because auto-stop calls `provider.stop` and writes
  the record, `status` is **not** read-only (MCP `readOnlyHint: false`); it
  never terminates or deletes anything.
- **`stop`** goes `running -> stopping -> stopped` via `provider.stop`. It is
  a no-op once the job is stopped or later.
- **`destroy`** stops first when the job is running, then
  `provider.terminate`, then `destroyed`. On a `launching` job it abandons
  the launch as described under Write-ahead reservation. On a `requested`
  or `reserved` job (no `instance_id`, nothing launched) it abandons the job
  without any provider call: `requested|reserved -> failed` (reason
  `abandoned`), then `failed -> destroyed`. `reconcile` then releases this
  job's ledger `reserved` amount (if one was written) with `actual_usd = 0`,
  so a reservation never has to be launched and spent to be freed. It is a
  no-op once the job is destroyed or reconciled.
- **`reconcile`** runs from `destroyed` or `failed`; a `failed` job with a
  known instance is terminated and destroyed first. On any other state it
  raises `ValueError`; in particular, a stuck `launching` job must be
  destroyed first. Steps:
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
- blocked by an unapproved budget, then the budget is approved, then
  `provision` with the same request (default `job_id`) gives `running` with
  one reservation. Its history shows `blocked -> requested` (reason `retry`);
- `fail_launch_after_create`: the job stays `launching` with the reservation
  held and no release. A second `provision` gives `running` on the same single
  instance. In a separate case, `destroy` on the stuck job terminates the
  leaked instance (`launching -> failed -> destroyed`), and `reconcile` then
  releases the reservation;
- `destroy` on a `reserved` job (and on a `requested` job after the ledger
  reservation was written) gives `failed` (reason `abandoned`) then
  `destroyed` with no provider call and no launch; `reconcile` then releases
  the full reservation, records `actual_usd = 0`, and `budget.remaining()`
  is back to its value before `provision`;
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

### API delegation budget (separate from host-plan usage)

Providers with deployment `api` (adapters `anthropic_api` and `openai_api` serving
via `agent-os orchestrate delegate --role inline`) are blocked with status
`budget_blocked` until the operator sets an API budget. Use:

```powershell
agent-os orchestrate api-budget set --total-usd N --call-cap-usd M
agent-os orchestrate api-budget set --total-usd N --call-cap-usd M --period monthly
agent-os orchestrate api-budget show    # spent and remaining
```

The `--period` option controls budget rollover: `total` (default; all spend ever recorded counts) or `monthly` (only spend since the start of the current UTC calendar month counts toward spent/remaining). Budgets saved before this change behave as `total`; `api-budget show` reports the active `period` and `period_start` timestamp.

This is a separate budget from host-plan (Claude Code / Codex subscription) usage
and from the GPU compute budget (`orchestrate budget`, budget.json/spend.jsonl).
Either provider alone is sufficient (set keys via `orchestrate api-key set anthropic|openai`).

Each API call's usage `cost_usd` is appended to `~/.agent-os/api-spend.jsonl` with these fields:
- `at`: timestamp (ISO-8601 UTC)
- `call_id`: unique call identifier
- `provider`: "anthropic" or "openai"
- `model`: the model used
- `amount_usd`: the call's usage cost (rounded to 6 decimals)
- `accuracy`: "exact" when the price is known, "unknown" otherwise
- `note`: optional annotation

Before an API call, `delegate()` makes a worst-case estimate (prompt characters / 4 as input tokens,
plus the provider's `max_tokens` option, default 8192, as output tokens, priced from model_value price evidence)
and blocks the call with status `budget_blocked` when that estimate exceeds the per-call cap or the remaining budget.
The estimate is recorded as `api_estimated_cost_usd`. When a model's price is unknown, no estimate is made,
and the after-call `api_call_cap_exceeded` flag still applies. Host-plan calls are never written
to `api-spend.jsonl` and the GPU compute budget is untouched.

## 14. FreeComputeBroker (OpenRouter free pool)

See `docs/free-compute-broker.md` for the design, data shapes, test plan, and
implementation order.

The FreeComputeBroker maximizes useful work on OpenRouter's volatile free-model
pool. It runs inside the existing router, budget, CAP/EVR, validator and
Research Radar primitives, with no second orchestration stack. All modules are
deterministic code over cached, versioned data; tests run against fixtures only.

### Modules (`src/agent_os/orchestrator/`)

- `free_catalog.py`: Fetch and cache OpenRouter free models; decide "free" via
  `is_free(pricing)` predicate (every raw pricing value parses to Decimal 0).
- `free_policy.py`: Load versioned provider-policy record; merge operator
  overrides; report staleness.
- `openrouter_account.py`: Read-only access to key, credit state, and rate
  limits behind `secrets://openrouter/default`; derive `high_allowance` flag
  from credits or ledger evidence.
- `free_quota.py`: Append-only quota ledger; daily budget, per-minute governor,
  reserve, retry budget, reset boundary; backfill eligibility.
- `free_specialization.py`: Per-(task_family × model) specialization records
  from ledger + CAP observations; Wilson bounds; proven/canary/unproven status.
- `free_metrics.py`: Metrics report (useful progress per request, validator
  acceptance, retries, escalations, paid fallbacks avoided, estimated paid cost
  avoided).
- `free_routing.py`: Low-risk/verifiable eligibility rule, data-policy check,
  model choice, escalation ladder, top-up alert evaluation.
- `free_swarm.py`: Bounded disposable fan-out where validation is cheap;
  checkpointable backfill queue for otherwise-expiring quota.

### CLI commands

```powershell
agent-os orchestrate free-compute catalog [--refresh]    # discovered models
agent-os orchestrate free-compute diff                   # changes since last fetch
agent-os orchestrate free-compute policy                 # versioned provider policy
agent-os orchestrate free-compute account                # read-only account state
agent-os orchestrate free-compute quota                  # ledger and governor status
agent-os orchestrate free-compute route <task.json>      # routing decision (free or escalate)
agent-os orchestrate free-compute specialization         # per-family model evidence
agent-os orchestrate free-compute metrics [--day]        # cost, progress, acceptance rates
agent-os orchestrate free-compute backfill               # queue status
agent-os orchestrate free-compute status                 # operator summary
```

### State location

**Runtime state** (derived, rebuildable, outside Git):
`<orchestrator_home>/free-compute/`:
- `catalog/snapshots/<snapshot_id>.json`: Versioned model discovery
- `catalog/latest.json`: Most recent snapshot
- `catalog/diffs.jsonl`: Consecutive snapshot diffs
- `account.json`: Last read-only account state (key never stored)
- `policy-overrides.json`: Operator overrides (optional)
- `ledger.jsonl`: Append-only free request attempt events
- `specialization.json`: Derived per-(task_family × model) records
- `backfill/queue.jsonl`, `backfill/checkpoints/<item_id>.json`: Backfill work items and checkpoints

**Provider policy** (reviewed, Git-backed, append-only):
`projects/personal-agent-os/orchestrator-os/records/provider-policy/openrouter-free.json`:
- Versioned allowance figures (daily requests at low/high tiers, RPM, reset
  boundary, credit threshold).
- Data-policy entries per model/revision, reviewed from OpenRouter's published
  data policies.
- Overrideable through `policy-overrides.json` (operator only).

### Allowance versioning and overrides

The provider-policy record in Git holds `{"schema_version": "...",
"versions": [<record>, ...]}`, with highest `version` as current. Each version
carries `free_rpm`, `daily_free_requests_low`, `daily_free_requests_high`,
`credit_threshold_usd`, `reset` (UTC boundary), `verified_at` (timestamp),
`verified_by` (source), `max_age_days`, and `data_policies` (reviewed per-model
entries).

These are **data, never constants**: no module hard-codes 20 RPM, 50 requests,
1000 requests, or $10 threshold.

**Overrides** are optional, in `<orchestrator_home>/free-compute/policy-overrides.json`
(operator only). `free_policy.effective()` merges the current policy version with
overrides for any numeric field, `reserve_requests`, `retry_budget`,
`backfill_window_hours`, `swarm_max_width`, `allowed_sensitivity`, or
`allow_training_endpoints`.

A policy record whose `verified_at` is older than `max_age_days` is marked
`stale`. Stale policy still governs quota (uses the low allowance), but can
never trigger a top-up alert.

### Top-up alert rule

`free_routing.top_up_status(account, policy)` evaluates whether to alert the
operator, returning `not_needed | recommended | unknown | blocked_by_policy`:

- **`not_needed`**: `account.high_allowance is true`. The account is eligible
  for the higher daily allowance; a low balance by itself never triggers an alert.
- **`recommended`** (the only status that alerts): **all** hold:
  - `account.high_allowance is false` via the credits basis (total purchased
    credits < policy's `credit_threshold_usd`).
  - Current policy is verified (not stale) with a non-null threshold.
  - No ledger-based discrepancy recorded.
  
  The alert names the exact shortfall (e.g. `shortfall_usd: 5.00`), the
  allowance it unlocks (low → high daily requests), policy source and
  verification date, and account read time. **Agent OS never purchases credits
  or enables auto-recharge.** The operator tops up in the OpenRouter console.
- **`unknown`**: `high_allowance` is `null`, policy is stale, purchased credits
  unreadable, or a ledger observed-cap discrepancy contradicts a credits-based
  false. No alert sent; reason and discrepancies shown in CLI/GUI.
- **`blocked_by_policy`**: Operator disabled free routing or no task family is
  eligible. A top-up would not help.

### Hard invariants (enforced by every module and assertion)

1. **Never purchase credits.** No code path POSTs to billing, checkout or
   payment endpoints. `openrouter_account.py` sends only GET requests to an
   allowlist (`/api/v1/models`, `/api/v1/key`, `/api/v1/credits`).
2. **Never enable auto-recharge.** No setting, flag or API call changes account
   configuration. The account adapter is read-only by construction.
3. **Never call a paid model.** A `route=free` decision names a model for which
   `free_catalog.is_free(pricing)` is true on the current snapshot. The broker
   only *decides*; escalation delegates to the existing router and its budget
   gate. Swarm/backfill re-check `is_free` on the latest snapshot immediately
   before dispatch.
4. **Never read or print secret values.** The key reference
   `secrets://openrouter/default` is resolved only inside the adapter's request
   builder and never returned, logged, cached, stored or put in an exception.
   Errors are redacted; status reports presence and source only.

## 15. Rented-GPU utilization (IMP-0015)

A rented pod's cost structure — fixed hourly rate regardless of request volume —
makes peak utilization critical. IMP-0015 adds concurrency tuning, keep-busy
scheduling, and multi-role coverage to squeeze maximum useful work per paid second.

### vLLM throughput settings

`pod_request()` sets throughput flags tuned for the model, GPU, and operator preferences:

- `--enable-prefix-caching`: enabled by default, caches KV prefixes across
  requests to maximize cache hits when IMP-0018's shared_prefix is available.
- `--enable-chunked-prefill`: enabled by default; processes input tokens in
  smaller batches to reduce latency variance under high concurrency.
- `--max-num-seqs N`: computed from the free KV-cache capacity. Formula:
  `free_kv_bytes = gpu_count * vram_gb * 1e9 * 0.90 - weight_gb * 1e9 * 1.1`,
  divided by `kv_bytes_per_token * (kv_dtype_bytes / 2) * avg_tokens`, where
  average tokens = context // 4 (sequences rarely fill the window). The result
  is clamped to [4, 256] and is the steady-state request concurrency budget.
- `--kv-cache-dtype fp8`: when the GPU supports it (H100, H200, H20, L4, L40,
  RTX 4090, RTX 6000 Ada, B200, RTX 5090), compresses KV cache from 2 bytes to
  1 byte per token, doubling max-num-seqs and prefix-cache utilization. Disabled
  by default on GPUs without fp8 hardware.

Every flag can be overridden: pass `vllm_overrides` to `pod_request()` with
keys `prefix_caching`, `chunked_prefill`, `max_num_seqs`, or `kv_cache_dtype`.
Overrides are stored at deployment and reported in `utilization_preview()`.

### Adaptive concurrency

The rented provider's `max_concurrency` limit starts at 4 and adapts from live
vLLM `/metrics` every tick (30 s), informed by:
- running and waiting request counts (zero queue → opportunity to grow);
- GPU KV-cache usage (70% threshold to raise, 90% to back off).

The `ConcurrencyPolicy` tunable defines behavior:
- `minimum: 2, maximum: 32`: hard bounds;
- `start: 4`: initial limit on each deployment;
- `step_up: 2`, `raise_after: 2`: raise the limit by 2 after 2 ticks with no
  queue, KV < 70% and running >= limit-1;
- `backoff_after: 1`: back off immediately on any waiting request (step down to
  limit-2) or KV >= 90% (halve to limit//2); hold when metrics are missing.

The state machine has hysteresis: a `raise` or `backoff` decision resets the
counter so each direction requires sustained evidence (e.g. 2 ticks in good
condition, 1 tick in bad). Decisions are recorded in telemetry for analysis.

### Keep the paid GPU busy

When attached runs are idle or between planning and execution, the rented
provider (via `gpu_keep_busy.useful_work`) looks for queued work in priority order:

1. **Reviews**: nodes in reviewer role, state READY or WAITING_FOR_REVIEW.
2. **Worker tasks**: implementer, test_author nodes, fast or balanced capability
   class, state READY or PENDING. (Repairer nodes are matched only if registered
   in the active roles; they are not registered for gpu_pod by default.)
3. **Backfill**: checkpointable items from the free-compute broker's backfill
   queue (see section 14), re-checked against `is_free()` immediately before dispatch.

Queued useful work restarts the idle timer once and keeps it running while
serving. Unrouted work the router ignores gets one `idle_minutes` grace period
before teardown. Paid idle — seconds with no user request running (tracked
separately) — has a target of 15% (DEFAULT_IDLE_TARGET) recorded in telemetry.
**The budget, deadline, and reaper safety checks still take precedence:** idle
teardown waits until nothing useful is queued, then counts down; the budget
watchdog deletes the pod before the next tick would cross 95% of the job cap; and
the reaper deletes orphan pods left by client crashes.

### Role coverage and shared-GPU limits

The rented provider is registered for every role its GPU class allows:
- `gpu_pod`: planner, inline, implementer, test_author, reviewer.
- `local` or `api`: planner, inline (read-only roles; no compute).

An interactive coding agent can share the same vLLM server concurrently, bounded
by `tier_concurrency`: heavy tiers (reasoning, etc.) are limited to 1 concurrent
request so both workflows — rented planning and live coding — can run at once.
**Open decision (noted in summary)**: whether to register a separate distinct
`foreman-reviewer` provider for reviews (dedicated queue, higher isolation) or
route reviews through the planner's concurrency pool.

### Weight caching (off by default)

`pod_request()` accepts an optional `weight_volume` (RunPod network volume ID).
When provided, the pod mounts the volume and sets `HF_HOME` to cache model
weights across pod starts, saving download time and cost on restart.

`weight_cache.cost_check()` compares storage cost per month against the savings
from avoiding repeated downloads:
- storage cost: `volume_gb * 0.07 $/GB/month` (RunPod's standard rate);
- download cost per start: `weight_gb / 0.5 GBPS * pod_hourly_usd / 3600` (0.5 GB/s is typical Hugging Face throughput);
- saves = (download cost per month) — (storage cost).

The preview reports `weight_cache.recommended: true` when `saves > 0`, and suggests the
volume size and estimated monthly savings. The feature is off by default (no volume
attached) and safe to leave off for short-lived runs.

### Shared-prefix stability (IMP-0018 integration)

When IMP-0018's `shared_prefix` is available in the run record, the rented
provider is designed to ensure every request to vLLM starts with exactly those
bytes before any per-request content. The `prefix_stability.stabilize()` function
exists for this purpose and handles whitespace repair and message structure
adjustments, but it is not yet wired into request building. The foreman currently
records the prefix fingerprint in telemetry only. Once integrated, no separator
will be added by stabilize (the run-level prefix is byte-stable), but the node
that builds requests to the rented model must keep a fixed separator between the
stable prefix and per-request text, and assert it in tests (DEC-0043 R5-3).

Prefix stability maximizes vLLM's prefix-cache hit rate by eliminating drift
from per-request formatting. The feature is active only when `shared_prefix` is
present; runs without it work normally. `utilization_preview()` reports
`prefix_stable: None` (unknown until a run attaches and its prefix is
fingerprinted in telemetry).

### Utilization reporting and preview

**Live utilization_view** (from `foreman_deploy.utilization_view()`) extends the
cost metrics with:
- `tokens_per_s`: generation throughput across all requests.
- `kv_usage_pct`: current GPU KV-cache occupancy (0–100).
- `prefix_cache_hit_pct`: (prefix cache hits) / (queries), when tracked.
- `concurrency_limit`: current adaptive concurrency limit.
- `paid_idle_pct`: fraction of paid time spent idle (no running or waiting
  requests). Derived from `PaidIdle.tick()` calls in the meter loop: each tick
  marks idle if `running + waiting == 0`.
- `idle_target_pct`: the 15% target.
- `meets_idle_target`: whether actual paid idle is at or under target.
- `usd_per_useful_request`: amortized cost per request; currently equal to
  `usd_per_request` (cost divided by all served requests).

**Deploy-time utilization_plan** (from `utilization_preview()`) shows the
expected plan:
- `planned_max_num_seqs`: the --max-num-seqs value that will be launched.
- `kv_cache_dtype`: fp8, fp16, or None.
- `prefix_caching`, `chunked_prefill`: flags enabled at launch.
- `roles`: role names from ROLES_BY_CLASS (planner, inline, implementer,
  test_author, reviewer for gpu_pod).
- `initial_concurrency`, `concurrency_bounds`: starting limit and min/max range.
- `idle_target_pct`: the 15% target.
- `prefix_stable`: None (will be fingerprinted once a run attaches).
- `weight_cache`: cost analysis result (`recommended`, `saves_usd_month`, etc.).

The preview is deterministic and makes no network call; it is safe to run before
deciding to deploy.
