// Simple Mode renderer. Uses api()/el()/toast() from app.js and the pure
// helpers in simple-core.js. Every control acknowledges a click immediately,
// then reports what it is waiting for; no policy lives here.
"use strict";

(function () {
  const core = window.SimpleCore;
  const S = { project: null, home: null, prep: null, prepTimer: null, homeTimer: null, pending: 0, lastRunId: null };

  function storageGet(key, fallback) { try { return localStorage.getItem(key) ?? fallback; } catch { return fallback; } }
  function storageSet(key, value) { try { localStorage.setItem(key, value); } catch { /* per-viewer convenience only */ } }

  // ------------------------------------------------------------ feedback

  // Wrap a user action: acknowledge now, say what we wait for, never freeze.
  async function act(button, action, label, fn) {
    const ack = core.acknowledge(action);
    const original = button ? button.innerHTML : null;
    if (button) { button.disabled = true; button.classList.add("pressed"); button.textContent = ack.buttonLabel; }
    setBusy(ack.status);
    S.pending += 1;
    const started = Date.now();
    const timer = setInterval(() => {
      const text = core.stillWorking(label, Date.now() - started);
      if (text) setBusy(text);
    }, 350);
    try {
      return await fn();
    } catch (error) {
      toast(`That did not work: ${error.message}`);
      return null;
    } finally {
      clearInterval(timer);
      S.pending -= 1;
      if (S.pending === 0) setBusy(null);
      if (button) { button.disabled = false; button.classList.remove("pressed"); button.innerHTML = original; }
    }
  }

  function setBusy(text) {
    $("busy").classList.toggle("hidden", !text);
    $("busy-text").textContent = text || "";
  }

  function showAdvice(message, target) {
    $("advice-text").textContent = message;
    $("advice").classList.remove("hidden");
    for (const node of document.querySelectorAll(".highlight")) node.classList.remove("highlight");
    const id = core.adviceElementId(target);
    const node = id && document.getElementById(id);
    if (node) {
      node.classList.add("highlight");
      node.scrollIntoView({ block: "center", behavior: "smooth" });
      node.focus({ preventScroll: true });
      setTimeout(() => node.classList.remove("highlight"), 6000);
    }
  }

  // ------------------------------------------------------------ loading

  async function loadHome() {
    const query = S.project ? `?project=${encodeURIComponent(S.project)}` : "";
    const home = await api(`home${query}`);
    S.home = home;
    if (!S.project && home.project) S.project = home.project;
    render(home);
    schedule();
    return home;
  }

  function schedule() {
    clearTimeout(S.homeTimer);
    const run = S.home && S.home.current_run;
    const live = (S.home && S.home.prep && S.home.prep.state === "running") || (run && ["WORKING", "INTERRUPTED"].includes(run.overall));
    S.homeTimer = setTimeout(() => loadHome().catch(() => schedule()), live ? 2000 : 8000);
  }

  function pollPrep(prepId) {
    clearTimeout(S.prepTimer);
    S.prepTimer = setTimeout(async () => {
      try {
        const prep = await api(`prep/${prepId}`);
        S.prep = prep;
        renderPrep(prep);
        if (prep.state === "running") { pollPrep(prepId); return; }
        setBusy(null);
        if (prep.state === "failed") showAdvice(prep.message, null);
        await loadHome();
      } catch (error) {
        pollPrep(prepId);
      }
    }, 300);
  }

  // ------------------------------------------------------------ rendering

  function render(home) {
    const picker = $("project-select");
    const ids = [...(home.projects || [])];
    if (!home.project) ids.unshift("");
    if (picker.options.length !== ids.length) {
      picker.replaceChildren(...ids.map((id) => el("option", { value: id }, id || "(this folder)")));
    }
    picker.value = home.project || "";
    $("s-project").textContent = home.project || String(home.repository || "").split(/[\\/]/).pop();
    $("s-project").title = home.repository || "";
    picker.closest("label").classList.toggle("hidden", !(home.projects || []).length);
    $("s-roadmap").textContent = core.roadmapLine(home.roadmap);
    $("s-stage-dots").replaceChildren(...((home.roadmap && home.roadmap.stages) || []).map((stage) =>
      el("span", { class: `dot st-${stage.status}`, title: `${stage.id} ${stage.title}: ${stage.plain_status}` })));
    if (home.next_stage) {
      $("s-next").textContent = `${home.next_stage.id} — ${home.next_stage.title}`;
      $("s-next-why").textContent = `Status in the roadmap: ${home.next_stage.plain_status}` + (home.skipped && home.skipped.length ? ` · skipped ${home.skipped.map((item) => item.stage).join(", ")} (another agent has unfinished work there)` : "");
    } else {
      $("s-next").textContent = home.roadmap ? "Nothing left: every eligible stage is complete" : "No roadmap file found";
      $("s-next-why").textContent = "";
    }
    const campaign = home.campaign || {};
    $("until-done").checked = storageGet("agent-os-until-done", "0") === "1";
    const control = core.controls(home);
    if (!S.pending) {
      $("continue-button").disabled = !control.continueEnabled;
      $("continue-label").textContent = control.continueLabel;
      $("continue-spinner").classList.toggle("hidden", !control.busy);
    }
    $("pause-button").disabled = !control.pauseEnabled;
    $("stop-button").disabled = !control.stopEnabled;
    $("resume-button").classList.toggle("hidden", !control.showResume);
    if (home.prep && home.prep.state === "running") renderPrep(home.prep);
    else if (home.current_run) renderRun(home.current_run);
    else $("run-panel").classList.toggle("hidden", !(S.prep && S.prep.state !== "done"));
    if (campaign.status && campaign.stop_reason && campaign.status !== "active" && home.current_run && home.current_run.overall === "DONE") {
      $("r-headline").textContent = `Finished. ${campaign.stop_reason}`;
    }
  }

  function renderPrep(prep) {
    $("run-panel").classList.remove("hidden");
    $("r-eyebrow").textContent = "AUTONOMOUS ROADMAP RUN";
    setOverall(prep.state === "failed" ? "STOPPED" : "STARTING");
    $("r-headline").textContent = prep.message;
    $("r-steps").replaceChildren(...prep.steps.map(stepItem));
    $("r-problems").replaceChildren();
    $("continue-label").textContent = prep.state === "running" ? "Starting…" : "CONTINUE ROADMAP";
  }

  function setOverall(overall) {
    const pill = $("r-overall");
    pill.textContent = overall;
    pill.className = `status-pill ${core.overallClass(overall)}`;
  }

  function stepItem(step) {
    return el("li", { class: `step ${step.status}` },
      el("span", { class: "icon", "aria-hidden": "true" }, core.stepIcon(step.status)),
      el("span", { class: "label" }, step.label),
      step.detail ? el("span", { class: "detail" }, step.detail) : null,
      el("span", { class: "sr-only" }, ` (${step.status})`));
  }

  function renderRun(view) {
    S.lastRunId = view.run_id;
    $("run-panel").classList.remove("hidden");
    $("r-eyebrow").textContent = view.stage ? "AUTONOMOUS ROADMAP RUN" : "TASK RUN";
    setOverall(view.overall);
    $("r-headline").textContent = view.headline;
    $("r-stage").textContent = view.stage ? `${view.stage.id} — ${view.stage.title}` : "Specific task (not from the roadmap)";
    $("r-task").textContent = view.current_task;
    $("r-tasks").textContent = view.tasks.total ? `${view.tasks.done} / ${view.tasks.total} tasks complete` : "planning…";
    $("r-steps").replaceChildren(...view.steps.map(stepItem));
    $("r-agents").replaceChildren(...view.agents.map((row) => el("tr", {},
      el("th", {}, row.agent), el("td", { class: `agent-${row.status.toLowerCase().replaceAll(" ", "-")}` }, row.status), el("td", { class: "muted" }, row.detail || ""))));
    $("r-warning").classList.toggle("hidden", !view.telemetry_warning);
    $("r-warning").textContent = view.telemetry_warning ? `Note: ${view.telemetry_warning}` : "";
    $("r-problems").replaceChildren(...view.problems.map(problemCard));
    const activity = $("r-activity");
    activity.replaceChildren(...view.activity.slice(-40).reverse().map((item) => el("li", {},
      el("span", { class: "t" }, new Date(item.at).toLocaleTimeString()), " — ", item.text)));
    renderEfficiency(view.efficiency);
    renderSummary(view.summary);
    $("r-advanced").textContent = JSON.stringify({ run_id: view.run_id, advice: view.advice, efficiency_files: view.efficiency && view.efficiency.report.files }, null, 2);
  }

  function renderEfficiency(eff) {
    if (!eff) { $("r-eff-rows").replaceChildren(); return; }
    $("r-eff-rows").replaceChildren(...eff.rows.map((raw) => {
      const row = core.effRow(raw);
      return el("tr", { title: row.help },
        el("th", {}, row.label, " ", el("span", { class: "help-dot", title: row.help, tabindex: "0", "aria-label": row.help }, "?")),
        el("td", { class: "num" }, row.value),
        el("td", {}, el("span", { class: `acc acc-${row.accuracy}` }, row.accuracy)));
    }));
    const files = eff.report.files || {};
    $("r-eff-files").textContent = files.events ? `Structured log: ${files.events} · Readable log: ${files.transcript}` : "";
  }

  function renderSummary(summary) {
    const box = $("r-summary");
    box.classList.toggle("hidden", !summary);
    if (!summary) return;
    const tests = summary.tests || {};
    const calls = Object.entries(summary.calls_by_agent || {}).map(([agent, count]) => `${agent} calls: ${count}`);
    const lines = [
      ["Completed", `${summary.tasks_completed} task(s)`],
      ["Files changed", summary.files_changed],
      ["Tests", tests.passed === null || tests.passed === undefined ? `${tests.runs || 0} test run(s)` : `${tests.passed} passed, ${tests.failed} failed` + (tests.reused ? ` (${tests.reused} result(s) reused)` : "")],
      ["Commits", summary.commits],
      ["Model calls", calls.join(" · ") || "none"],
      ["Local / no-model steps", summary.local_operations],
      ["Tokens used (provider-reported)", (summary.tokens_used_exact === null ? "not reported by the providers" : core.formatNumber(summary.tokens_used_exact)) + (summary.calls_without_token_report ? ` (${summary.calls_without_token_report} call(s) did not report usage)` : "")],
      ["Estimated tokens avoided", summary.tokens_avoided_estimate === null ? "no defensible estimate" : `${core.formatNumber(summary.tokens_avoided_estimate)} (estimate)`],
      ["Model calls avoided", summary.model_calls_avoided],
    ];
    if (summary.landed) lines.push(["Saved to main branch", summary.landed.ok ? "yes" : `no: ${summary.landed.reason}`]);
    else if (summary.how_to_land) lines.push(["Result", `on its own branch (${summary.how_to_land})`]);
    box.replaceChildren(el("h3", {}, summary.title), el("dl", { class: "kv wide" }, ...lines.flatMap(([key, value]) => [el("dt", {}, key), el("dd", {}, String(value ?? "—"))])));
  }

  function problemCard(card) {
    const key = card.gate_id || card.node || "final";
    const note = card.recommended.needs_note ? el("input", { placeholder: "Your answer for the agent" }) : null;
    const run = (item, button) => act(button, item.decision ? "decide" : item.action || "retry", item.label, () => resolve(card, item, note ? note.value : null));
    const recommended = el("button", { class: "primary", id: `problem-${key}-recommended`, onclick: (event) => run(card.recommended, event.currentTarget) }, card.recommended.label);
    return el("div", { class: "problem" },
      el("div", { class: "problem-title" }, card.title),
      el("p", {}, card.what),
      el("p", { class: "unchanged" }, card.changed),
      note,
      el("div", { class: "muted" }, "Recommended:"),
      el("div", { class: "row" }, recommended, el("span", { class: "muted" }, card.recommended.does)),
      card.options.length ? el("div", { class: "muted" }, "Other options:") : null,
      ...card.options.map((option) => el("div", { class: "row" },
        el("button", { onclick: (event) => run(option, event.currentTarget) }, option.label), el("span", { class: "muted" }, option.does))),
      el("div", { class: "row" }, el("button", { class: "ghost", onclick: () => explain(card) }, "Explain This To Me")),
      el("details", {}, el("summary", {}, "Advanced Details"), el("pre", {}, JSON.stringify(card.advanced, null, 2))));
  }

  async function resolve(card, choice, note) {
    const runId = S.lastRunId;
    if (choice.decision) {
      await api(`runs/${runId}/decide`, { gate_id: card.gate_id, approve: choice.decision === "approve", note });
    } else if (choice.action === "retry") {
      await api(`runs/${runId}/retry`, { node_id: card.node });
    } else if (choice.action === "retry_final") {
      await api(`runs/${runId}/retry`, { node_id: "_final" });
    } else if (choice.action === "fresh") {
      const result = await api(`runs/${runId}/fresh`, {});
      if (result && result.prep) { S.prep = result.prep; renderPrep(result.prep); pollPrep(result.prep.id); }
    }
    await loadHome();
  }

  function explain(card) {
    $("explain-title").textContent = card.title;
    $("explain-body").textContent = card.explain || card.what;
    $("explain-dialog").showModal();
  }

  // ------------------------------------------------------------ actions

  async function continueRoadmap(button) {
    const untilDone = $("until-done").checked;
    // Immediate, local acknowledgement: the run panel appears with steps.
    S.prep = core.optimisticPrep();
    renderPrep(S.prep);
    await act(button, "continue", "starting the roadmap run", async () => {
      const result = await api("roadmap/continue", { project: S.project, auto_until_done: untilDone, preference: storageGet("agent-os-preference", "") || null });
      S.prep = result.prep;
      renderPrep(result.prep);
      pollPrep(result.prep.id);
    });
    // Keep the "Starting…" state until the preparation reports back.
    $("continue-button").disabled = true;
    $("continue-label").textContent = "Starting…";
  }

  async function runControl(button, action) {
    const runId = S.home && S.home.current_run && S.home.current_run.run_id;
    if (!runId) { showAdvice("There is no run to control right now. Press Continue Roadmap to start one.", "continue"); return; }
    await act(button, action, `${action} the run`, async () => { await api(`runs/${runId}/${action}`, {}); await loadHome(); });
  }

  async function tellMeWhatToPress(button) {
    await act(button, "help", "checking the current state", async () => {
      const home = await loadHome();
      showAdvice(home.advice.message, home.advice.target);
    });
  }

  function setMode(mode) {
    const advanced = mode === "advanced";
    $("simple-mode").classList.toggle("hidden", advanced);
    $("advanced-mode").classList.toggle("hidden", !advanced);
    $("mode-simple").classList.toggle("on", !advanced);
    $("mode-advanced").classList.toggle("on", advanced);
    $("mode-simple").setAttribute("aria-pressed", String(!advanced));
    $("mode-advanced").setAttribute("aria-pressed", String(advanced));
    storageSet("agent-os-mode", mode);
  }

  async function loadUsage() {
    const usage = await api("usage");
    $("usage-rows").replaceChildren(...usage.rows.map((raw) => {
      const row = core.effRow(raw);
      return el("tr", { title: row.help },
        el("th", {}, row.label, " ", el("span", { class: "help-dot", title: row.help, tabindex: "0", "aria-label": row.help }, "?")),
        el("td", { class: "num" }, row.value),
        el("td", {}, el("span", { class: `acc acc-${row.accuracy}` }, row.accuracy)));
    }));
  }

  function wireSimple() {
    $("usage-panel").addEventListener("toggle", (event) => { if (event.target.open) act(null, "refresh", "adding up model usage", loadUsage); });
    $("continue-button").addEventListener("click", (event) => continueRoadmap(event.currentTarget));
    $("help-button").addEventListener("click", (event) => tellMeWhatToPress(event.currentTarget));
    $("advice-close").addEventListener("click", () => $("advice").classList.add("hidden"));
    $("pause-button").addEventListener("click", (event) => runControl(event.currentTarget, "pause"));
    $("resume-button").addEventListener("click", (event) => runControl(event.currentTarget, "resume"));
    $("stop-button").addEventListener("click", (event) => runControl(event.currentTarget, "stop"));
    $("view-progress-button").addEventListener("click", () => {
      $("run-panel").classList.remove("hidden");
      $("run-panel").scrollIntoView({ behavior: "smooth" });
      if (!S.home || !S.home.current_run) showAdvice("No run has started yet. Press Continue Roadmap to start one.", "continue");
    });
    $("start-task-button").addEventListener("click", () => { $("task-form").classList.toggle("hidden"); $("task-goal").focus(); });
    $("task-cancel").addEventListener("click", () => $("task-form").classList.add("hidden"));
    $("task-start").addEventListener("click", (event) => {
      const goal = $("task-goal").value.trim();
      if (!goal) { showAdvice("Type what the agents should do first, then press Start This Task.", null); return; }
      act(event.currentTarget, "start-task", "starting your task", async () => {
        await api("runs", { goal, project: S.project, start_recommended: true, auto_continue: true, preference: storageGet("agent-os-preference", "") || undefined });
        $("task-form").classList.add("hidden");
        $("task-goal").value = "";
        await loadHome();
      });
    });
    $("until-done").addEventListener("change", (event) => storageSet("agent-os-until-done", event.target.checked ? "1" : "0"));
    $("settings-button").addEventListener("click", () => { $("set-preference").value = storageGet("agent-os-preference", "balanced"); $("settings-dialog").showModal(); });
    $("settings-close").addEventListener("click", () => { storageSet("agent-os-preference", $("set-preference").value); $("settings-dialog").close(); });
    $("explain-close").addEventListener("click", () => $("explain-dialog").close());
    $("project-select").addEventListener("change", (event) => { S.project = event.target.value; act(null, "refresh", "loading the project", loadHome); });
    $("mode-simple").addEventListener("click", () => setMode("simple"));
    $("mode-advanced").addEventListener("click", () => setMode("advanced"));
  }

  wireSimple();
  setMode(storageGet("agent-os-mode", "simple"));
  act(null, "refresh", "reading the project and roadmap", loadHome);
})();
