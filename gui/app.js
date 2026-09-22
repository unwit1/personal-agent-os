// Agent OS Orchestrator control GUI.
// A thin client: every control calls the local API, which calls the engine.
// No orchestration policy lives here.
"use strict";

const TOKEN = document.querySelector('meta[name="agent-os-token"]').content;
const $ = (id) => document.getElementById(id);
let currentRun = null;
let stream = null;
let providers = [];

async function api(path, body) {
  const options = { headers: { "X-Agent-OS-Token": TOKEN } };
  if (body !== undefined) {
    options.method = "POST";
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const response = await fetch(`/api/${path}`, options);
  const data = await response.json().catch(() => ({ error: response.statusText }));
  if (!response.ok || (data && data.error)) throw new Error((data && data.error) || response.statusText);
  return data;
}

function toast(message) {
  const el = $("toast");
  el.textContent = message;
  el.classList.remove("hidden");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => el.classList.add("hidden"), 4500);
}

async function guarded(fn) {
  try { return await fn(); } catch (error) { toast(error.message); }
}

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "class") node.className = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else if (value !== undefined && value !== null) node.setAttribute(key, value);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

const badge = (state) => el("span", { class: `badge s-${state}` }, state);

// ---------------------------------------------------------------- runs list

async function refreshRuns(select) {
  const runs = await api("runs");
  const picker = $("run-select");
  const chosen = select ?? picker.value;
  picker.replaceChildren(el("option", { value: "" }, "— new task —"));
  for (const run of runs) {
    picker.append(el("option", { value: run.run_id }, `${run.state} · ${run.goal.slice(0, 60)} (${run.run_id})`));
  }
  picker.value = chosen || "";
}

function openRun(runId) {
  currentRun = runId || null;
  if (stream) { stream.close(); stream = null; }
  const visible = Boolean(currentRun);
  for (const id of ["run", "agents", "events", "findings", "final"]) $(id).classList.toggle("hidden", !visible);
  $("new-task").classList.toggle("hidden", visible);
  $("event-log").replaceChildren();
  if (!visible) { $("gates").classList.add("hidden"); return; }
  guarded(async () => render(await api(`runs/${currentRun}`)));
  stream = new EventSource(`/api/runs/${encodeURIComponent(currentRun)}/stream?token=${encodeURIComponent(TOKEN)}`);
  stream.addEventListener("status", (event) => render(JSON.parse(event.data)));
  stream.addEventListener("events", (event) => appendEvents(JSON.parse(event.data)));
}

// ---------------------------------------------------------------- rendering

function render(run) {
  if (!run || run.run_id !== currentRun) return;
  $("run-goal").textContent = run.goal;
  $("run-meta").textContent = `${run.run_id} · ${run.project || "unregistered project"} · ${run.repository} @ ${run.base_ref || run.base_commit.slice(0, 10)} · preference ${run.preference} · launches ${run.launches}/${run.launch_budget}`;
  $("run-state").replaceWith(Object.assign(badge(run.state), { id: "run-state" }));
  const pct = run.progress.total ? Math.round((100 * run.progress.passed) / run.progress.total) : 0;
  $("progress-bar").style.width = `${run.state === "COMPLETE" ? 100 : pct}%`;
  $("run-reason").textContent = `${run.progress.passed}/${run.progress.total} stages passed · ${run.progress.integrated} integrated` + (run.state_reason ? ` · ${run.state_reason}` : "");
  $("auto-toggle").checked = Boolean(run.auto_continue);
  const driver = run.gui_driver || {};
  $("driver").textContent = driver.alive
    ? "driving in this GUI process"
    : run.driver && run.driver.active ? `driven by another process (${run.driver.owner})` : driver.error ? `driver stopped: ${driver.error}` : "not being driven — press Drive or Resume";
  renderGates(run);
  renderAgents(run);
  renderFindings(run);
  renderFinal(run);
}

function renderGates(run) {
  const open = run.gates.filter((gate) => gate.status === "open");
  $("gates").classList.toggle("hidden", open.length === 0);
  $("gate-list").replaceChildren(...open.map((gate) => {
    const note = el("input", { placeholder: "note / decision for the agent (optional)" });
    const decide = (approve) => guarded(async () => render(await api(`runs/${currentRun}/decide`, { gate_id: gate.id, approve, note: note.value })));
    return el("div", { class: "gate" },
      el("div", {}, el("span", { class: "gate-kind" }, gate.kind.replaceAll("_", " ")), gate.node ? ` · ${gate.node}` : "", ` · ${gate.id}`),
      el("div", {}, gate.reason),
      note,
      el("div", { class: "row" },
        el("button", { class: "primary", onclick: () => decide(true) }, gate.kind === "consequential_repository_write" ? "Approve Merge" : "Approve"),
        el("button", { class: "danger", onclick: () => decide(false) }, "Reject")));
  }));
}

function renderAgents(run) {
  $("agent-cards").replaceChildren(...run.nodes.map((node) => {
    const evidence = (node.validation && node.validation.evidence) || [];
    const reviewers = (node.review && node.review.reviewers) || [];
    const actions = el("div", { class: "actions" });
    if (["FAILED_FINAL", "FAILED_RETRYABLE", "CANCELLED"].includes(node.state)) {
      actions.append(el("button", { onclick: () => guarded(async () => render(await api(`runs/${currentRun}/retry`, { node_id: node.id }))) }, "Retry"));
    }
    if (node.execution_path === "model" && node.state !== "PASSED") {
      actions.append(el("button", { onclick: () => reassign(node) }, "Reassign"));
    }
    if (["implementer", "test_author"].includes(node.role) && node.state === "PASSED" && !node.integrated) {
      actions.append(el("button", { onclick: () => guarded(async () => render(await api(`runs/${currentRun}/review-again`, { node_id: node.id }))) }, "Review Again"));
    }
    return el("div", { class: "card" },
      el("div", { class: "card-head" },
        el("div", {}, el("div", { class: "role" }, node.role.replace("_", " ") + (node.subject ? ` of ${node.subject}` : "")), el("div", { class: "card-title" }, node.id)),
        badge(node.state)),
      el("div", { class: "muted" }, node.goal),
      el("dl", { class: "kv" },
        el("dt", {}, "provider"), el("dd", {}, node.provider || (node.execution_path === "deterministic" ? "deterministic" : "—")),
        el("dt", {}, "model"), el("dd", {}, node.model || "—"),
        el("dt", {}, "effort"), el("dd", {}, `${node.effort}${node.provider_effort ? ` → ${node.provider_effort}` : ""} · ${node.capability_class}${node.capability_class !== node.requested_capability_class ? ` (from ${node.requested_capability_class})` : ""}`),
        el("dt", {}, "branch"), el("dd", {}, node.branch || "—"),
        el("dt", {}, "scope"), el("dd", {}, node.scope.length ? node.scope.join(", ") : "whole repository"),
        el("dt", {}, "attempts"), el("dd", {}, `${node.attempts} · retries ${node.retries} · escalations ${node.escalations}${node.integrated ? " · integrated" : ""}`)),
      node.selection_reason ? el("div", { class: "muted" }, `route: ${node.selection_reason}${node.overridden ? " (override)" : ""}`) : null,
      node.wait_reason ? el("div", { class: "wait" }, node.wait_reason) : null,
      evidence.length ? el("div", {}, evidence.map((item) => el("span", { class: `chip ${item.passed ? "ok" : "bad"}`, title: item.detail || "" }, `${item.passed ? "✓" : "✗"} ${item.name}`))) : null,
      reviewers.length ? el("div", {}, reviewers.map((review) => el("span", { class: "chip" }, `review r${review.round}: ${review.verdict} by ${review.provider}`))) : null,
      actions.childElementCount ? actions : null);
  }));
}

function renderFindings(run) {
  const rows = [];
  for (const node of run.nodes) {
    for (const finding of (node.review && node.review.findings) || []) {
      rows.push(el("tr", {},
        el("td", {}, node.id),
        el("td", { class: `sev-${finding.severity}` }, finding.severity),
        el("td", {}, finding.path || ""),
        el("td", {}, finding.summary, finding.recommended_action ? el("div", { class: "muted" }, `→ ${finding.recommended_action}`) : null),
        el("td", {}, finding.disposition + (finding.disposition_reason ? `: ${finding.disposition_reason}` : ""))));
    }
  }
  $("finding-rows").replaceChildren(...(rows.length ? rows : [el("tr", {}, el("td", { colspan: 5, class: "muted" }, "No review findings yet."))]));
}

function renderFinal(run) {
  const body = [];
  const final = run.final || {};
  if (final.validation) {
    body.push(el("div", {}, badge(final.validation.passed ? "PASSED" : "FAILED"), " completion validators"));
    body.push(el("div", {}, (final.validation.evidence || []).map((item) => el("span", { class: `chip ${item.passed ? "ok" : "bad"}`, title: item.detail || "" }, `${item.passed ? "✓" : "✗"} ${item.name}`))));
  } else {
    body.push(el("div", { class: "muted" }, "Completion validators run once every stage has passed and been integrated."));
  }
  const integration = run.integration || {};
  body.push(el("dl", { class: "kv" },
    el("dt", {}, "branch"), el("dd", {}, integration.branch || "—"),
    el("dt", {}, "head"), el("dd", {}, (integration.head || "—").slice(0, 12)),
    el("dt", {}, "merged"), el("dd", {}, (integration.merged || []).join(", ") || "—")));
  if (final.summary) body.push(el("div", {}, el("strong", {}, "Land with: "), el("code", {}, final.summary.how_to_land)));
  if (final.landed) body.push(el("div", { class: final.landed.ok ? "" : "wait" }, final.landed.ok ? `Landed on base at ${String(final.landed.commit).slice(0, 12)}` : `Not landed: ${final.landed.reason}`));
  body.push(el("div", { class: "muted" }, `usage: ${run.usage.workers} worker run(s), ${run.usage.input_tokens} in / ${run.usage.output_tokens} out tokens (when providers report them)`));
  $("final-body").replaceChildren(...body);
}

function appendEvents(events) {
  const log = $("event-log");
  for (const event of events) {
    log.append(el("li", {}, el("span", { class: "t" }, event.at.slice(11, 19)), el("span", { class: "k" }, event.type), event.node ? `[${event.node}] ` : "", event.detail || ""));
  }
  log.scrollTop = log.scrollHeight;
}

// ---------------------------------------------------------------- actions

function reassign(node) {
  const names = providers.map((item) => item.id).join(", ");
  const provider = prompt(`Reassign ${node.id} to provider (${names}):`, providers[0] ? providers[0].id : "");
  if (!provider) return;
  const model = prompt("Model (blank = registry recommendation):", "") || null;
  const effort = prompt("Effort (none/low/medium/high, blank = stage default):", "") || null;
  guarded(async () => render(await api(`runs/${currentRun}/reassign`, { node_id: node.id, provider, model, effort })));
}

async function createRun(recommended) {
  const goal = $("goal").value.trim();
  if (!goal) { toast("Describe the goal first."); return; }
  const run = await api("runs", {
    goal,
    repository: $("repository").value.trim(),
    project: $("project").value.trim(),
    validators: $("validators").value,
    preference: $("preference").value,
    start_recommended: recommended,
    auto_continue: $("new-auto").checked,
  });
  await refreshRuns(run.run_id);
  openRun(run.run_id);
}

async function loadProviders() {
  const data = await api("providers");
  providers = data.providers || [];
  const select = $("ov-provider");
  select.replaceChildren(el("option", { value: "" }, "(recommended provider)"), ...providers.map((item) => el("option", { value: item.id }, `${item.id}${item.probe && !item.probe.available ? " (unavailable)" : ""}`)));
  return data;
}

function wire() {
  $("run-select").addEventListener("change", (event) => openRun(event.target.value));
  $("start-recommended").addEventListener("click", () => guarded(() => createRun(true)));
  $("create-manual").addEventListener("click", () => guarded(() => createRun(false)));
  for (const button of document.querySelectorAll("[data-action]")) {
    button.addEventListener("click", () => guarded(async () => render(await api(`runs/${currentRun}/${button.dataset.action}`, {}))));
  }
  $("auto-toggle").addEventListener("change", (event) => guarded(async () => render(await api(`runs/${currentRun}/auto-continue`, { enabled: event.target.checked }))));
  const override = (clear) => guarded(async () => {
    const scope = $("ov-scope").value;
    const body = { provider: $("ov-provider").value, model: $("ov-model").value.trim(), effort: $("ov-effort").value, clear };
    if (scope.startsWith("role:")) body.role = scope.slice(5);
    render(await api(`runs/${currentRun}/override`, body));
    toast(clear ? "Override cleared" : "Override saved; it applies to the next launches");
  });
  $("ov-apply").addEventListener("click", () => override(false));
  $("ov-clear").addEventListener("click", () => override(true));
  $("providers-button").addEventListener("click", () => guarded(async () => {
    $("providers-body").textContent = JSON.stringify(await loadProviders(), null, 2);
    $("providers-dialog").showModal();
  }));
  $("providers-suggest").addEventListener("click", () => guarded(async () => { $("providers-body").textContent = JSON.stringify(await api("providers/suggest", { write: false }), null, 2); }));
  $("providers-write").addEventListener("click", () => guarded(async () => { $("providers-body").textContent = JSON.stringify(await api("providers/suggest", { write: true }), null, 2); await loadProviders(); }));
  $("providers-close").addEventListener("click", () => $("providers-dialog").close());
}

wire();
guarded(async () => { await loadProviders(); await refreshRuns(); });
