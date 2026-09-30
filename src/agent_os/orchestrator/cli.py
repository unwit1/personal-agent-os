"""`agent-os orchestrate ...` -- headless control of orchestrated runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from . import service


TERMINAL_EXIT = {"COMPLETE": 0, "PAUSED": 3, "APPROVAL_REQUIRED": 4, "BLOCKED": 5, "FAILED": 5}


def register(commands: argparse._SubParsersAction) -> None:
    orchestrate = commands.add_parser("orchestrate", help="multi-agent coding orchestrator")
    actions = orchestrate.add_subparsers(dest="orchestrate_action", required=True)

    providers = actions.add_parser("providers", help="show configured providers and routing recommendations")
    providers.add_argument("--suggest", action="store_true", help="probe installed coding CLIs and suggest registry entries")
    providers.add_argument("--write", action="store_true", help="with --suggest: add missing entries to the machine-local registry")
    providers.add_argument("--force", action="store_true", help="with --write: replace existing entries of the same id")
    providers.add_argument("--path")

    create = actions.add_parser("create", help="create a run")
    _create_arguments(create)
    create.add_argument("--start", action="store_true")
    create.add_argument("--auto-continue", action="store_true")

    recommended = actions.add_parser("start-recommended", help="plan, start with Auto Continue, and drive until a stop state")
    _create_arguments(recommended)
    recommended.add_argument("--max-seconds", type=float)
    recommended.add_argument("--no-drive", action="store_true", help="create and start, but return without driving")

    for name in ("status", "result", "step", "events", "pause", "resume", "stop"):
        parser = actions.add_parser(name)
        parser.add_argument("run_id")
        if name == "events":
            parser.add_argument("--after", type=int, default=0)
    actions.add_parser("list")

    start = actions.add_parser("start")
    start.add_argument("run_id")
    start.add_argument("--auto-continue", dest="auto_continue", action="store_true", default=None)
    start.add_argument("--no-auto-continue", dest="auto_continue", action="store_false")

    run = actions.add_parser("run", help="drive a run in the foreground (Auto Continue: until a stop state)")
    run.add_argument("run_id")
    run.add_argument("--max-seconds", type=float)
    run.add_argument("--max-ticks", type=int)

    for name in ("approve", "reject"):
        parser = actions.add_parser(name)
        parser.add_argument("run_id")
        parser.add_argument("gate_id")
        parser.add_argument("--note")

    for name in ("retry", "review-again"):
        parser = actions.add_parser(name)
        parser.add_argument("run_id")
        parser.add_argument("node_id")

    reassign = actions.add_parser("reassign")
    reassign.add_argument("run_id")
    reassign.add_argument("node_id")
    reassign.add_argument("--provider", required=True)
    reassign.add_argument("--model")
    reassign.add_argument("--effort")

    override = actions.add_parser("override", help="provider/model/effort override for the run, a role, or a node")
    override.add_argument("run_id")
    override.add_argument("--provider")
    override.add_argument("--model")
    override.add_argument("--effort")
    target = override.add_mutually_exclusive_group()
    target.add_argument("--role")
    target.add_argument("--node")
    override.add_argument("--clear", action="store_true")

    road = actions.add_parser("roadmap", help="show roadmap progress and the next eligible stage (no model call)")
    road.add_argument("--project")
    road.add_argument("--repo")

    cont = actions.add_parser("continue-roadmap", help="Continue Roadmap: resume unfinished work or start the next roadmap stage, then drive it")
    cont.add_argument("--project")
    cont.add_argument("--repo")
    cont.add_argument("--until-done", action="store_true", help="Auto Continue Until Done: after each stage completes and lands, start the next")
    cont.add_argument("--fresh", action="store_true", help="set aside unfinished runs instead of resuming them")
    cont.add_argument("--preference", choices=["economy", "balanced", "quality"])
    cont.add_argument("--no-drive", action="store_true", help="prepare and start, but return without driving")

    report = actions.add_parser("report", help="efficiency report for a run from its telemetry (tokens, calls, context, avoided work)")
    report.add_argument("run_id")
    report.add_argument("--transcript", action="store_true", help="print the human-readable run transcript instead")

    bench = actions.add_parser("benchmark", help="repeatable token-efficiency benchmark (offline by default; --live uses real providers)")
    bench.add_argument("--scenario", action="append", help="run only these scenarios (repeatable)")
    bench.add_argument("--live", action="store_true", help="use the machine's real providers (costs usage) for the small-code-change scenario")
    bench.add_argument("--out", help="directory for results.json and report.md")

    usage = actions.add_parser("usage-report", help="cross-run token usage report from run telemetry (provider-reported numbers)")
    usage.add_argument("--since", help="ISO timestamp; only events at or after it")
    usage.add_argument("--include-benchmarks", action="store_true", help="also count benchmark runs")

    models_cmd = actions.add_parser("models", help="model catalog: current tier models, new/outdated models, proposals (local + official online sources; no model call)")
    models_cmd.add_argument("--refresh", action="store_true", help="check sources now")
    models_cmd.add_argument("--offline", action="store_true", help="with --refresh: local sources only")
    trial_cmd = actions.add_parser("model-trial", help="try a model for a tier on a real small task (real calls; spends usage)")
    trial_cmd.add_argument("--provider", required=True)
    trial_cmd.add_argument("--model", required=True)
    trial_cmd.add_argument("--tier", required=True, choices=["fast", "balanced", "reasoning", "frontier"])
    decide_cmd = actions.add_parser("model-proposal", help="apply or dismiss a model proposal (apply writes the provider registry, with a backup)")
    decide_cmd.add_argument("proposal_id")
    decide_cmd.add_argument("decision", choices=["apply", "dismiss"])

    pbench = actions.add_parser("planner-bench", help="measure planner token use and plan quality per prompt/tool variant (real calls; spends usage)")
    pbench.add_argument("--project")
    pbench.add_argument("--repo", default=".")
    pbench.add_argument("--provider", default="claude-code")
    pbench.add_argument("--variant", action="append")

    over = actions.add_parser("overhead", help="measure each coding CLI's fixed per-call context cost (real calls; spends usage)")
    over.add_argument("--provider", action="append", help="provider id(s); default all enabled")
    over.add_argument("--variant", action="append", help="option variant(s) to measure; default all")
    over.add_argument("--repo", default=".")
    over.add_argument("--capability-class", default="fast")

    dlg = actions.add_parser("delegate", help="one read-only task through the router with an output contract; records capability evidence (real call)")
    dlg.add_argument("--task-family", required=True, help="capability-evidence task family, e.g. implementation_status_classification")
    dlg.add_argument("--prompt-file", required=True)
    dlg.add_argument("--contract", help="JSON file: output contract (see delegate.check_contract)")
    dlg.add_argument("--capability-class", default="fast")
    dlg.add_argument("--effort", default="low")
    dlg.add_argument("--provider")
    dlg.add_argument("--model")
    dlg.add_argument("--repo", default=".")
    dlg.add_argument("--timeout", type=int, default=900)
    dlg.add_argument("--out", help="write the validated result JSON here")
    dlg.add_argument("--attach", action="append", help="glob under --repo to inline as untrusted-data documents (repeatable; FND-0011)")
    dlg.add_argument("--attach-mode", default="datamark", choices=["datamark", "delimit"])
    dlg.add_argument("--role", default="analyst", choices=["analyst", "inline"], help="inline: the prompt carries all needed context (direct API workers may serve it)")
    dlg.add_argument("--require", action="append", metavar="KEY=VALUE", help="workload requirement on provider profiles, e.g. deployment=local,gpu_pod or refusal_profile=low,abliterated (repeatable)")
    dlg.add_argument("--prefer", action="append", metavar="KEY=VALUE", help="soft preference, e.g. refusal_profile=abliterated (becomes prefer_refusal_profile)")

    key = actions.add_parser("api-key", help="store or check a provider API key in the OS keyring (never in files)")
    key.add_argument("action", choices=["set", "status", "delete"])
    key.add_argument("provider", choices=["anthropic", "openai"])

    sec = actions.add_parser("secrets", help="provider-neutral secret references secrets://<provider>/<profile> (keyring or env; values never printed)")
    sec.add_argument("action", choices=["set", "status", "delete", "setup"])
    sec.add_argument("ref", nargs="?", help="e.g. secrets://runpod/default (setup: optional; default walks every known credential)")
    sec.add_argument("--gui", action="store_true", help="set: masked pop-up dialog instead of a terminal prompt")
    sec.add_argument("--reprompt", action="store_true", help="setup: also prompt for credentials that are already configured")
    sec.add_argument("--from-env", metavar="VAR", help="with set: read the value from this environment variable instead of a hidden prompt")

    madd = actions.add_parser("model-add", help="register an OpenAI-compatible endpoint (vLLM/Ollama/LM Studio/llama.cpp/TGI; open-weight or abliterated) in the machine-local registry; preview unless --write")
    madd.add_argument("--id", required=True, help="provider id, e.g. local-abliterated")
    madd.add_argument("--base-url", required=True, help="server root, e.g. http://127.0.0.1:8000 (the adapter appends /v1/chat/completions)")
    madd.add_argument("--model", required=True, help="exact model id the server expects")
    madd.add_argument("--classes", default="fast,balanced", help="capability classes this model may serve (comma list)")
    madd.add_argument("--refusal-profile", default="standard", choices=["standard", "low", "abliterated", "unknown"])
    madd.add_argument("--deployment", choices=["subscription", "api", "serverless", "gpu_pod", "local"], help="default: local for a loopback URL, else api")
    madd.add_argument("--open-weights", action=argparse.BooleanOptionalAction, default=None)
    madd.add_argument("--license")
    madd.add_argument("--revision", help="exact model revision served (e.g. the catalog's commit sha); keys capability evidence by revision")
    madd.add_argument("--context-window", type=int)
    madd.add_argument("--secret-ref", help="secrets://<provider>/<profile> holding the endpoint's API key, if it needs one")
    madd.add_argument("--cost", type=float, default=0.25, help="relative cost per call vs the registry's other providers (default 0.25)")
    madd.add_argument("--max-concurrency", type=int, default=2)
    madd.add_argument("--roles", default="inline", help="comma list; add analyst so orchestrate eval / eval-queue can score it (prompts stay self-contained)")
    madd.add_argument("--write", action="store_true")
    madd.add_argument("--force", action="store_true", help="replace an existing entry with the same id")
    madd.add_argument("--path", help="registry file (default: the machine-local registry)")

    actions.add_parser("refusals", help="refusal/non-answer telemetry by provider/model/refusal profile (no model call)")

    evq = actions.add_parser("eval-queue", help="evaluate queued catalog models once served: plan is deterministic; run calls orchestrate eval (real calls, bounded)")
    evq.add_argument("action", choices=["plan", "run"])
    evq.add_argument("--model", help="only this catalog model id")
    evq.add_argument("--incumbent", help="baseline route provider[:model][@class] (default: cheapest other provider for the class)")
    evq.add_argument("--max-calls", type=int, default=6, help="run: per-suite model-call budget")

    rdr = actions.add_parser("radar", help="Model Research Radar: scan the Hugging Face Hub into a local model catalog and queue eval candidates (no model call, no weight downloads)")
    rdr.add_argument("action", choices=["scan", "catalog"])
    rdr.add_argument("--search", help="scan: one ad-hoc search instead of the default scans")
    rdr.add_argument("--pipeline", help="scan: pipeline tag, e.g. text-generation, text-to-image, automatic-speech-recognition")
    rdr.add_argument("--sort", default="trendingScore")
    rdr.add_argument("--limit", type=int, default=20)
    rdr.add_argument("--min-downloads", type=int, default=10000, help="scan: adoption floor for queueing an eval")
    rdr.add_argument("--modality", help="catalog: filter, e.g. audio")
    rdr.add_argument("--refusal-profile", help="catalog: filter by declared refusal hint, e.g. abliterated")

    qte = actions.add_parser("quote", help="no-spend quote: API vs GPU pod vs serverless, low/expected/high, with the budget gate (no model call, no provisioning)")
    qte.add_argument("--workload", required=True, help="JSON file: workload (workload.py)")
    qte.add_argument("--options", help="JSON file: list of priced options (kind api|gpu_pod|serverless; see quote.py)")
    qte.add_argument("--gpu-from", choices=["runpod"], help="add live GPU offers from this provider's read-only inventory (no spend)")
    qte.add_argument("--gen-tps", type=float, help="with --gpu-from: generation tokens/s for this model on one GPU (measured; not invented)")
    qte.add_argument("--train-tps", type=float, help="with --gpu-from: training tokens/s for this job on one GPU")
    qte.add_argument("--limit", type=int, default=5, help="with --gpu-from: cheapest N qualifying offers")
    qte.add_argument("--model", help="with --gpu-from and no --gen-tps/--train-tps: use recorded throughput for this model per GPU (orchestrate throughput)")

    thr = actions.add_parser("throughput", help="serving-throughput evidence per model x GPU x engine; measure is real calls to your own endpoint")
    thr.add_argument("action", choices=["measure", "record", "show"])
    thr.add_argument("--provider", help="measure: registered OpenAI-compatible provider id")
    thr.add_argument("--model", help="model id (measure: defaults to the provider's first model)")
    thr.add_argument("--gpu", help="GPU display name as shown by orchestrate compute inventory, e.g. A100 PCIe")
    thr.add_argument("--engine", help="serving engine, e.g. vllm-0.30")
    thr.add_argument("--revision")
    thr.add_argument("--requests", type=int, default=8)
    thr.add_argument("--concurrency", type=int, default=4)
    thr.add_argument("--max-tokens", type=int, default=256)
    thr.add_argument("--tps", type=float, help="record: tokens/s to store")
    thr.add_argument("--kind", default="generation", choices=["generation", "training"])
    thr.add_argument("--source", default="measured", choices=["measured", "benchmark", "assumed"])
    thr.add_argument("--no-record", action="store_true", help="measure: print only")

    bud = actions.add_parser("budget", help="operator compute budget: show, or set project budget and per-job hard cap (operator action; history kept)")
    bud.add_argument("action", choices=["show", "set"])
    bud.add_argument("--project-usd", type=float)
    bud.add_argument("--job-cap-usd", type=float)
    bud.add_argument("--note")

    cmp_ = actions.add_parser("compute", help="read-only GPU inventory and pricing (RunPod first); never provisions or spends")
    cmp_.add_argument("action", choices=["inventory"])
    cmp_.add_argument("--provider", default="runpod")
    cmp_.add_argument("--refresh", action="store_true", help="ignore the 6 h cache")
    cmp_.add_argument("--min-vram", type=float, default=0.0)

    fsh = actions.add_parser("foreman-shadow", help="shadow foreman: a candidate model proposes a DAG + classes for a run; compare/report are deterministic, propose is one real call")
    fsh.add_argument("action", choices=["propose", "compare", "report"])
    fsh.add_argument("run", nargs="?", help="run id (propose/compare)")
    fsh.add_argument("--provider", help="foreman provider id (default: routed by --require/--prefer)")
    fsh.add_argument("--require", action="append", metavar="KEY=VALUE")
    fsh.add_argument("--prefer", action="append", metavar="KEY=VALUE")

    fmn = actions.add_parser("foreman", help="session foreman: deploy a Hugging Face model on a RunPod GPU within the job budget and use it as the planner for new runs")
    fmn.add_argument("action", choices=["use", "preview", "deploy", "status", "stop", "eval", "strategy", "reap", "evidence"],
                     help="eval: score the live foreman's per-task model choices and efficiency on labeled planning cases (real calls)")
    fmn.add_argument("link", nargs="?", help="preview/deploy: Hugging Face model link or org/name; use: claude, chatgpt, openrouter or local")
    fmn.add_argument("--model", help="use: pin one model (e.g. opus, gpt-6.1-sol, or a local model id)")
    fmn.add_argument("--base-url", help="use local: the OpenAI-compatible server, e.g. http://127.0.0.1:11434")
    fmn.add_argument("--secret-ref", help="use local: secrets://<provider>/<profile> holding the server's API key, if it needs one")
    fmn.add_argument("--job-usd", type=float, help="job budget; default: the machine budget's per-job cap")
    fmn.add_argument("--idle-minutes", type=int, default=15)
    fmn.add_argument("--coding-agent", action="store_true", help="deploy/preview: also serve the model as a Codex CLI coding agent (64k context, tool calling; bigger GPU)")
    fmn.add_argument("--provider", help="eval: provider id to evaluate (default: the ready session foreman)")
    fmn.add_argument("--case", action="append", help="eval: only these case ids")
    fmn.add_argument("--split", choices=["dev", "holdout", "dev2", "holdout2", "dev_all", "holdout_all", "all"], default="dev", help="eval: dev* cases may be used for tuning; holdout* never are")

    ctx = actions.add_parser("context-anatomy", help="IMP-0018 Phase 0: tokens per prompt section, fan-out duplication and context amplification for a finished run (no model call)")
    ctx.add_argument("run", help="run id (or a run directory)")
    ctx.add_argument("--harness-tokens", type=int, default=6000, help="per-call harness overhead to assume (codex ~9000, claude ~6000)")

    cap = actions.add_parser("capability", help="aggregate capability observations into CAP records (no model call)")
    cap.add_argument("--write", action="store_true", help="write CAP records to projects/personal-agent-os/orchestrator-os/records/capability/")
    cap.add_argument("--floor", type=float, default=0.9)

    ckpt = actions.add_parser("checkpoint", help="Orchestrator OS continuation checkpoint + next prompt (no model call)")
    ckpt.add_argument("--write", action="store_true", help="persist ORCH-NNNN and next-prompt.md")
    ckpt.add_argument("--show", action="store_true", help="show the latest persisted checkpoint")
    actions.add_parser("next-prompt", help="print the current generated next prompt")

    guard = actions.add_parser("control-check", help="check paths (or the working-tree diff) against the protected control plane")
    guard.add_argument("paths", nargs="*")
    guard.add_argument("--base", default="main", help="with no paths: diff against this ref")
    guard.add_argument("--allow", action="append", default=[])

    ev = actions.add_parser("eval", help="incumbent vs candidate over an EVS suite; writes an EVR (test suites: git refs; case suites: routes)")
    ev.add_argument("--suite", required=True, help="EVS id, e.g. EVS-CONTROL-PLANE")
    ev.add_argument("--incumbent", help="baseline git ref (test suites, default main) or route (case suites, default first --route)")
    ev.add_argument("--candidate", action="append", default=[], help="candidate git ref (test suites), repeatable")
    ev.add_argument("--route", action="append", default=[], help="provider[:model][@class] (case suites), repeatable")
    ev.add_argument("--margin", type=float, help="noninferiority margin (default: policy promotion.noninferiority_margin_default)")
    ev.add_argument("--operator-holdout", action="store_true", help="operator only: allow protected holdout splits")
    ev.add_argument("--no-write", action="store_true", help="do not write the EVR record")
    ev.add_argument("--sequential", action="store_true")
    ev.add_argument("--samples", type=int, default=1, help="case suites: calls per base route (+verify variants reuse them)")
    ev.add_argument("--max-calls", type=int, help="refuse the run if it needs more model calls than this")

    actions.add_parser("context-report", help="context-utility: attachment reference rates and always-unreferenced attachments (no model call)")

    corp = actions.add_parser("corpus", help="external attack-corpus registry: list, or import a corpus as data into .agent-local (no model call)")
    corp.add_argument("corpus_action", choices=["list", "import"])
    corp.add_argument("corpus_id", nargs="?")
    corp.add_argument("--write", action="store_true", help="import: fetch and store the corpus locally (gitignored) and update the registry")
    corp.add_argument("--derive", action="store_true", help="import: also derive local EVS-SECURITY fixtures from the imported goals")
    corp.add_argument("--limit", type=int, default=8)

    mine = actions.add_parser("mining", help="failure/success signature clusters and coverage gaps (no model call)")
    mine.add_argument("--write", action="store_true", help="write projects/personal-agent-os/orchestrator-os/mining-report.json")

    tr = actions.add_parser("trace", help="export a run's telemetry as OpenTelemetry OTLP/JSON spans (GenAI conventions; no content exported)")
    tr.add_argument("run_id")
    tr.add_argument("--out", help="write the OTLP/JSON document here (otherwise printed)")

    simp = actions.add_parser("simplify", help="simplification engine: component view + dead/duplicate/dependency/prior-art candidates (no model call; deletes nothing)")
    simp.add_argument("--write", action="store_true", help="write projects/personal-agent-os/orchestrator-os/simplification-report.json")

    mut = actions.add_parser("mutate", help="mutation testing: mutate a module in throwaway worktrees and run the named tests (no model call)")
    mut.add_argument("module", help="repo-relative path, e.g. src/agent_os/orchestrator/control_plane.py")
    mut.add_argument("--tests", action="append", required=True, help="test module, e.g. tests.test_orchestrator_control_plane (repeatable)")
    mut.add_argument("--ref", default="HEAD")
    mut.add_argument("--function", action="append", help="limit mutants to these functions")
    mut.add_argument("--workers", type=int, default=4)
    mut.add_argument("--limit", type=int)

    pa = actions.add_parser("prior-art", help="open-source prior-art registry: lookup, discovery queries, staleness, metadata refresh (no model call)")
    pa.add_argument("action", choices=["lookup", "queries", "stale", "refresh", "validate"])
    pa.add_argument("terms", nargs="*", help="problem description (lookup/queries) or entry ids (refresh)")
    pa.add_argument("--write", action="store_true", help="refresh: write updated activity facts")

    evc = actions.add_parser("eval-cases", help="generate deterministic development cases for a task family (no model call)")
    evc.add_argument("--family", required=True, choices=["affected_test_selection"])
    evc.add_argument("--base", default="HEAD", help="commit the labels are traced at")
    evc.add_argument("--limit", type=int, default=40)
    evc.add_argument("--workers", type=int, default=4)
    evc.add_argument("--no-write", action="store_true")

    gui = actions.add_parser("gui", help="serve the local control GUI and API")
    gui.add_argument("--host", default="127.0.0.1")
    gui.add_argument("--port", type=int, default=8765)
    gui.add_argument("--no-browser", action="store_true")
    gui.add_argument("--project", help="registered project shown on the Simple Mode home screen")
    gui.add_argument("--repo", help="repository path for Simple Mode when the project is not registered")


def _create_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--goal", required=True)
    parser.add_argument("--repo", help="path inside the target Git repository")
    parser.add_argument("--project", help="registered Agent OS project id")
    parser.add_argument("--tasks", help="JSON file with an explicit task list")
    parser.add_argument("--policy", help="JSON file with run policy overrides")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="policy override; VALUE is parsed as JSON when possible")
    parser.add_argument("--validator", action="append", default=[], help="default validator command (shell string), repeatable")
    parser.add_argument("--run-id")


def _policy(args: argparse.Namespace) -> dict[str, Any]:
    policy: dict[str, Any] = {}
    if args.policy:
        policy.update(json.loads(Path(args.policy).read_text(encoding="utf-8-sig")))
    for item in args.set:
        key, _, raw = item.partition("=")
        try:
            policy[key.strip()] = json.loads(raw)
        except json.JSONDecodeError:
            policy[key.strip()] = raw
    if args.validator:
        policy["default_validators"] = [
            *policy.get("default_validators", []),
            *({"kind": "command", "command": command} for command in args.validator),
        ]
    return policy


def _tasks(args: argparse.Namespace) -> list[dict[str, Any]] | None:
    if not args.tasks:
        return None
    data = json.loads(Path(args.tasks).read_text(encoding="utf-8-sig"))
    return data.get("tasks") if isinstance(data, dict) else data


def dispatch(args: argparse.Namespace, emit) -> int:
    action = args.orchestrate_action
    if action == "providers":
        emit(service.suggest_providers(args.write, args.path, args.force) if args.suggest else service.providers())
        return 0
    if action == "create":
        emit(service.create(args.goal, args.repo, args.project, _tasks(args), _policy(args), run_id=args.run_id, start=args.start, auto_continue=True if args.auto_continue else None))
        return 0
    if action == "start-recommended":
        policy = _policy(args)
        tasks = _tasks(args)
        if tasks:
            summary = service.create(args.goal, args.repo, args.project, tasks, {**policy, "auto_continue": True}, run_id=args.run_id, start=True, auto_continue=True)
        else:
            summary = service.start_recommended(args.goal, args.repo, args.project, policy, run_id=args.run_id)
        if args.no_drive:
            emit(summary)
            return 0
        final = service.engine().run_loop(summary["run_id"], max_seconds=args.max_seconds, owner="cli")
        emit(final)
        return TERMINAL_EXIT.get(final["state"], 0)
    if action == "list":
        emit(service.list_runs())
        return 0
    if action == "status":
        emit(service.status(args.run_id))
        return 0
    if action == "result":
        emit(service.result(args.run_id))
        return 0
    if action == "events":
        emit(service.events(args.run_id, args.after))
        return 0
    if action == "step":
        emit(service.step(args.run_id))
        return 0
    if action == "start":
        emit(service.engine().start(args.run_id, args.auto_continue))
        return 0
    if action in {"pause", "resume", "stop"}:
        emit(service.control(args.run_id, action))
        return 0
    if action == "run":
        final = service.engine().run_loop(args.run_id, max_seconds=args.max_seconds, max_ticks=args.max_ticks, owner="cli")
        emit(final)
        return TERMINAL_EXIT.get(final["state"], 0)
    if action in {"approve", "reject"}:
        emit(service.decide(args.run_id, args.gate_id, action == "approve", args.note))
        return 0
    if action == "retry":
        emit(service.retry(args.run_id, args.node_id))
        return 0
    if action == "review-again":
        emit(service.review_again(args.run_id, args.node_id))
        return 0
    if action == "reassign":
        emit(service.reassign(args.run_id, args.node_id, args.provider, args.model, args.effort))
        return 0
    if action == "override":
        emit(service.override(args.run_id, args.provider, args.model, args.effort, args.role, args.node, args.clear))
        return 0
    if action == "roadmap":
        from .roadmap import overview

        emit(overview(service.engine(), args.project, args.repo))
        return 0
    if action == "continue-roadmap":
        import threading

        from . import models
        from .roadmap import continue_roadmap, drive_campaign

        # Keep the model catalog current without delaying the run.
        threading.Thread(target=lambda: models.refresh_if_stale(), name="agent-os-model-check", daemon=True).start()
        engine = service.engine()
        result = continue_roadmap(engine, args.project, args.repo, auto_until_done=args.until_done, preference=args.preference, fresh=args.fresh)
        if args.no_drive or result["action"] not in {"started", "resumed"}:
            emit(result)
            return 0 if result["action"] != "error" else 2
        if args.until_done:
            campaign = drive_campaign(engine, args.project, args.repo)
            emit({**result, "campaign": campaign, "final": engine.status(campaign.get("current_run") or result["run_id"])["state"]})
            return 0
        final = engine.run_loop(result["run_id"], owner="cli")
        emit({**result, "final_state": final["state"], "state_reason": final.get("state_reason")})
        return TERMINAL_EXIT.get(final["state"], 0)
    if action == "report":
        engine = service.engine()
        if args.transcript:
            path = engine.ledger.paths(args.run_id)[1]
            print(path.read_text(encoding="utf-8") if path.exists() else f"no transcript at {path}")
            return 0
        emit(engine.efficiency(args.run_id))
        return 0
    if action == "benchmark":
        from .benchmark import run_benchmark

        report = run_benchmark(args.scenario, live=args.live, out_dir=Path(args.out) if args.out else None)
        emit({"files": report["files"], "totals": report["totals"], "scenarios": [{key: item[key] for key in ("scenario", "scenario_passed", "model_calls", "model_calls_avoided", "local_operations", "cache_hits", "escalations", "runtime_s")} for item in report["scenarios"]]})
        return 0 if report["totals"]["passed"] == report["totals"]["scenarios"] else 1
    if action == "usage-report":
        from .usage_report import report

        emit(report(since=args.since, include_benchmarks=args.include_benchmarks))
        return 0
    if action == "models":
        from . import models

        emit(models.refresh(online=not args.offline) if args.refresh else models.view())
        return 0
    if action == "model-trial":
        from . import models

        emit(models.trial(args.provider, args.model, args.tier))
        return 0
    if action == "model-proposal":
        from . import models

        emit(models.decide(args.proposal_id, args.decision == "apply"))
        return 0
    if action == "planner-bench":
        from .overhead import measure_planner

        emit(measure_planner(args.repo, args.project, provider=args.provider, variants=args.variant))
        return 0
    if action == "overhead":
        from .overhead import measure

        emit(measure(args.provider, repository=args.repo, capability_class=args.capability_class, variants=args.variant))
        return 0
    if action == "delegate":
        from .delegate import delegate
        from .model_profile import parse_pairs

        contract = json.loads(Path(args.contract).read_text(encoding="utf-8")) if args.contract else None
        outcome = delegate(Path(args.prompt_file).read_text(encoding="utf-8"), task_family=args.task_family, capability_class=args.capability_class, effort=args.effort, contract=contract, provider=args.provider, model=args.model, cwd=args.repo, timeout_seconds=args.timeout, role=args.role, attachments=args.attach, attach_mode=args.attach_mode,
                           requirements=parse_pairs([*(args.require or []), *(f"prefer_{item}" for item in (args.prefer or []))]))
        if args.out and outcome.get("result") is not None:
            Path(args.out).write_text(json.dumps(outcome["result"], indent=2), encoding="utf-8")
        emit({key: value for key, value in outcome.items() if key != "result"})
        return 0 if outcome["status"] == "passed" else 6
    if action == "capability":
        from . import capability

        records = capability.summarize(capability.read_observations(), floor=args.floor)
        emit({"records": records, "written": capability.write_records(records) if args.write else []})
        return 0
    if action == "checkpoint":
        from . import continuation

        if args.show:
            emit(continuation.latest() or {"error": "no checkpoint yet"})
            return 0
        checkpoint = continuation.build()
        emit({**checkpoint, "written": continuation.write(checkpoint) if args.write else None})
        return 0
    if action == "next-prompt":
        from . import continuation

        latest = continuation.latest()
        print(latest["next_prompt"] if latest else "No checkpoint yet: run `agent-os orchestrate checkpoint --write`.")
        return 0
    if action == "control-check":
        import subprocess

        from . import control_plane

        def git_lines(*argv: str) -> list[str]:
            return subprocess.run(["git", *argv], capture_output=True, text=True, check=False).stdout.splitlines()

        # Tracked changes against the base plus new, untracked files.
        paths = args.paths or sorted(set(git_lines("diff", "--name-only", args.base)) | set(git_lines("ls-files", "--others", "--exclude-standard")))
        result = control_plane.check(paths, args.allow)
        evidence = control_plane.negative_evidence_check(Path("."), args.base, paths, args.allow)
        emit({**result, "checked": len(paths), "negative_evidence": evidence})
        return 0 if result["passed"] and evidence["passed"] else 7
    if action == "secrets":
        import getpass
        import os

        from . import secret_refs

        if args.action == "setup":
            from .secret_prompt import setup

            emit(setup([args.ref] if args.ref else None, skip_configured=not args.reprompt))
            return 0
        if not args.ref:
            from .secret_prompt import CREDENTIALS

            emit([secret_refs.status(item["ref"]) for item in CREDENTIALS] if args.action == "status" else {"error": "ref required"})
            return 0 if args.action == "status" else 2
        if args.action == "status":
            emit(secret_refs.status(args.ref))
        elif args.action == "delete":
            emit(secret_refs.delete(args.ref))
        else:
            if args.gui:
                from .secret_prompt import tk_prompt

                value = tk_prompt(f"Agent OS - {args.ref}", f"Value for {args.ref} (stored in the OS keyring; never printed)") or ""
            else:
                value = os.environ.get(args.from_env, "") if args.from_env else getpass.getpass(f"value for {args.ref} (input hidden): ")
            emit(secret_refs.store(args.ref, value))
        return 0
    if action == "model-add":
        from .model_profile import endpoint_entry

        entry = endpoint_entry(args.id, base_url=args.base_url, model=args.model, classes=[item.strip() for item in args.classes.split(",") if item.strip()],
                               refusal_profile=args.refusal_profile, deployment=args.deployment, open_weights=args.open_weights, license=args.license,
                               context_window=args.context_window, secret_ref=args.secret_ref, cost=args.cost, max_concurrency=args.max_concurrency,
                               roles=[item.strip() for item in args.roles.split(",") if item.strip()], revision=args.revision)
        result = service.add_model_endpoint(entry, write=args.write, path=args.path, force=args.force)
        emit(result)
        return 1 if result.get("error") else 0
    if action == "foreman-shadow":
        from . import foreman
        from .model_profile import parse_pairs

        if args.action == "report":
            emit(foreman.report())
            return 0
        if not args.run:
            emit({"error": "run id required"})
            return 2
        if args.action == "propose":
            requirements = parse_pairs([*(args.require or []), *(f"prefer_{item}" for item in (args.prefer or []))])
            emit(foreman.propose(args.run, provider=args.provider, requirements=requirements))
            return 0
        from .store import RunStore

        record = RunStore().load(args.run)
        emit([foreman.compare(record, item) for item in foreman.load_proposals(args.run)])
        return 0
    if action == "context-anatomy":
        from . import context_anatomy
        from .store import RunStore

        target = Path(args.run)
        run_dir = target if target.is_dir() else RunStore().run_dir(args.run)
        emit(context_anatomy.analyze_run(run_dir, args.harness_tokens))
        return 0
    if action == "foreman":
        from . import budget as budget_lib
        from .foreman_deploy import manager

        if args.action == "use":
            emit(manager().use(str(args.link or ""), model=args.model, base_url=args.base_url, secret_ref=args.secret_ref))
            return 0
        if args.action in {"preview", "deploy"} and not args.link:
            emit({"error": "a Hugging Face link is required"})
            return 2
        if args.action == "preview":
            job = args.job_usd if args.job_usd is not None else budget_lib.effective(None).get("job_hard_cap_usd") or 0
            emit(manager().preview(args.link, float(job), coding_agent=args.coding_agent))
        elif args.action == "deploy":  # foreground: meters and tears down before returning
            emit(manager().deploy(args.link, job_cap_usd=args.job_usd, idle_minutes=args.idle_minutes, background=False, coding_agent=args.coding_agent))
        elif args.action == "stop":
            emit(manager().stop("stopped from the CLI"))
        elif args.action == "evidence":  # saved foreman evals -> CAP observations (idempotent)
            from . import foreman_eval

            emit(foreman_eval.backfill())
        elif args.action == "reap":  # safe to schedule every few minutes
            emit(manager().reap())
        elif args.action == "strategy":
            from . import foreman_strategy

            reports = foreman_strategy._eval_reports(None)
            emit({"host": foreman_strategy.host_models(), "models": foreman_strategy.strategy_table(reports=reports),
                  "foreman_ranking": foreman_strategy.recommend_foreman(reports)})
        elif args.action == "eval":
            from . import foreman_eval

            emit(foreman_eval.run(args.provider, cases=args.case, split=args.split))
        else:
            emit(manager().status())
        return 0
    if action == "quote":
        from . import quote as quote_lib
        from .workload import normalize_workload, to_requirements

        workload = normalize_workload(json.loads(Path(args.workload).read_text(encoding="utf-8")))
        options = json.loads(Path(args.options).read_text(encoding="utf-8")) if args.options else []
        notes = []
        if args.gpu_from:
            from . import compute

            stock = compute.inventory(args.gpu_from)
            rate_for = None
            if args.model and not (args.gen_tps or args.train_tps):
                from . import throughput

                rate_for = throughput.lookup(args.model, "training" if workload["type"] in {"training", "fine_tune", "adapter_training"} else "generation")
            gpu = compute.gpu_options(stock.get("offers") or [], workload, gen_tokens_per_second=args.gen_tps, train_tokens_per_second=args.train_tps,
                                      limit=args.limit, rate_for=rate_for)
            options += gpu
            if stock.get("error"):
                notes.append(f"{args.gpu_from} inventory unavailable: {stock['error']}")
            elif not gpu:
                notes.append("no GPU options priced: pass --gen-tps/--train-tps or --model with recorded throughput (never invented), or lower resources.vram_gb")
        if not options:
            emit({"error": "no options to quote", "notes": notes})
            return 2
        from . import budget

        result = quote_lib.quote(workload, options, budget.effective(workload.get("budget")))
        result["notes"] = notes
        result["routing_requirements"] = to_requirements(workload)
        emit(result)
        return 0
    if action == "budget":
        from . import budget

        if args.action == "show":
            emit(budget.show())
            return 0
        if args.project_usd is None or args.job_cap_usd is None:
            emit({"error": "set needs --project-usd and --job-cap-usd"})
            return 2
        emit(budget.set_budget(args.project_usd, args.job_cap_usd, note=args.note))
        return 0
    if action == "compute":
        from . import compute

        stock = compute.inventory(args.provider, refresh=args.refresh)
        stock["offers"] = [offer for offer in stock.get("offers") or [] if (offer.get("vram_gb") or 0) >= args.min_vram]
        emit(stock)
        return 0
    if action == "radar":
        from . import radar

        if args.action == "catalog":
            emit(radar.catalog_summary(modality=args.modality, refusal_profile=args.refusal_profile, limit=args.limit))
            return 0
        scans = None
        if args.search or args.pipeline:
            scans = [{"name": "ad-hoc", "search": args.search, "pipeline_tag": args.pipeline, "sort": args.sort, "limit": args.limit}]
        emit(radar.scan(scans, min_downloads=args.min_downloads))
        return 0
    if action == "throughput":
        from . import throughput

        if args.action == "show":
            rows = throughput.load()
            emit([row for row in rows if not args.model or row.get("model") == args.model])
            return 0
        if args.action == "record":
            emit(throughput.record(model=args.model, gpu=args.gpu, tokens_per_second=args.tps, kind=args.kind, engine=args.engine,
                                   revision=args.revision, source=args.source))
            return 0
        from .router import ProviderRegistry

        provider = ProviderRegistry().get(args.provider or "")
        if not provider or provider.get("adapter") != "openai_api":
            emit({"error": f"provider {args.provider!r} is not a registered openai_api endpoint (see orchestrate model-add)"})
            return 2
        model = args.model or next(iter(provider["models"].values()), None)
        result = throughput.measure(provider, model, requests=args.requests, concurrency=args.concurrency, max_tokens=args.max_tokens)
        if result["tokens_per_second"] and args.gpu and not args.no_record:
            result["recorded"] = throughput.record(model=model, gpu=args.gpu, tokens_per_second=result["tokens_per_second"], engine=args.engine,
                                                   revision=args.revision, concurrency=args.concurrency, source="measured")
        elif result["tokens_per_second"] and not args.gpu:
            result["note"] = "pass --gpu to record this measurement for quotes"
        emit(result)
        return 0
    if action == "eval-queue":
        from . import evalqueue

        if args.action == "plan":
            emit(evalqueue.plan(args.model, incumbent=args.incumbent))
        else:
            emit(evalqueue.run(args.model, incumbent=args.incumbent, max_calls=args.max_calls))
        return 0
    if action == "refusals":
        from pathlib import Path as _Path

        from . import refusal
        from .store import orchestrator_home

        emit(refusal.summary(_Path(orchestrator_home())))
        return 0
    if action == "api-key":
        import getpass
        import os

        from .adapters import http_api

        adapter = {"anthropic": http_api.AnthropicApiAdapter, "openai": http_api.OpenAiCompatibleAdapter}[args.provider]
        if args.action == "set":
            secret = getpass.getpass(f"{args.provider} API key (input hidden): ").strip()
            if not secret:
                emit({"ok": False, "error": "empty key"})
                return 2
            http_api.store_key(adapter.keyring_user, secret)
        elif args.action == "delete":
            import keyring

            try:
                keyring.delete_password(http_api.KEYRING_SERVICE, adapter.keyring_user)
            except Exception:
                pass
        present = bool(http_api.read_key(adapter.env_var, adapter.keyring_user))
        emit({"provider": args.provider, "key_present": present, "source": "env" if os.environ.get(adapter.env_var) else ("keyring" if present else None),
              "note": "run `agent-os orchestrate providers` to see the API worker (role inline)"})
        return 0
    if action == "context-report":
        from . import context_utility

        emit(context_utility.report())
        return 0
    if action == "corpus":
        from . import corpus

        if args.corpus_action == "list":
            emit({"corpora": [{k: entry.get(k) for k in ("id", "name", "license", "status", "revision", "contamination_risk", "task_families")} for entry in corpus.load_registry().get("corpora", [])]})
            return 0
        if args.corpus_id != "XC-agentdojo":
            emit({"error": "only XC-agentdojo has an importer so far"})
            return 2
        summary = corpus.import_agentdojo(write=args.write)
        if summary.get("ok") and args.write:
            corpus.apply_import_to_registry(summary)
            if args.derive:
                summary["derived"] = corpus.derive_injection_fixtures(limit=args.limit)
        emit(summary)
        return 0 if summary.get("ok") else 6
    if action == "mining":
        from . import mining

        report = mining.build()
        emit({key: report[key] for key in ("totals", "needs_coverage", "top_failure_signatures", "success_patterns")} | {"written": mining.write(report) if args.write else None})
        return 0
    if action == "trace":
        from . import trace

        emit(trace.export(args.run_id, out=Path(args.out) if args.out else None))
        return 0
    if action == "simplify":
        from . import simplify

        report = simplify.build()
        emit({key: report[key] for key in ("totals", "largest", "dead_module_candidates", "unused_public_functions", "duplicates", "dependencies", "prior_art_matches")} | {"written": simplify.write(report) if args.write else None})
        return 0
    if action == "mutate":
        from . import mutation

        result = mutation.run(args.module, args.tests, ref=args.ref, only_functions=set(args.function) if args.function else None, workers=args.workers, limit=args.limit)
        emit(result)
        return 0 if result.get("score") == 1.0 else 10
    if action == "prior-art":
        from . import prior_art

        text = " ".join(args.terms)
        if args.action == "lookup":
            emit({"problem": text, "matches": prior_art.lookup(text)})
        elif args.action == "queries":
            emit({"problem": text, "queries": prior_art.queries(text)})
        elif args.action == "stale":
            emit({"stale": prior_art.stale()})
        elif args.action == "refresh":
            emit({"changes": prior_art.refresh(list(args.terms), write=args.write)})
        else:
            problems = prior_art.validate()
            emit({"ok": not problems, "problems": problems})
            return 0 if not problems else 9
        return 0
    if action == "eval-cases":
        from . import eval as evaluation

        case_file = evaluation.generate_test_selection_cases(args.base, limit=args.limit, workers=args.workers, write=not args.no_write)
        emit({key: value for key, value in case_file.items() if key != "cases"} | {"case_count": len(case_file["cases"]), "empty_labels": sum(1 for case in case_file["cases"] if not case["expected_tests"])})
        return 0
    if action == "eval":
        from . import eval as evaluation

        record = evaluation.run(args.suite, incumbent=args.incumbent, candidates=args.candidate, routes=args.route, operator_holdout=args.operator_holdout, write=not args.no_write, margin=args.margin, parallel=not args.sequential, samples=args.samples, max_calls=args.max_calls)
        emit(record)
        return 0 if record["outcome"] in {"improved", "noninferior"} else 8
    if action == "gui":
        from .server import serve

        return serve(args.host, args.port, open_browser=not args.no_browser, project=args.project, repository=args.repo)
    raise ValueError(f"unknown orchestrate action {action}")
