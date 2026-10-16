// Simple Mode renderer. Uses api()/el()/toast() from app.js and the pure
// helpers in simple-core.js. Every control acknowledges a click immediately,
// then reports what it is waiting for; no policy lives here.
"use strict";

(function () {
  const core = window.SimpleCore;
  const S = { project: null, repository: null, repos: [], home: null, prep: null, prepTimer: null, homeTimer: null, pending: 0, lastRunId: null };

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
    const query = S.repository ? `?repository=${encodeURIComponent(S.repository)}` : S.project ? `?project=${encodeURIComponent(S.project)}` : "";
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
    const folder = String(home.repository || "").split(/[\\/]/).pop();
    $("repo-name").textContent = folder || home.project || "Choose a repository";
    $("repo-button").title = `${home.repository || ""} (click to switch repository)`;
    $("s-project").textContent = home.project || folder;
    $("s-project").title = home.repository || "";
    $("s-roadmap").textContent = core.roadmapLine(home.roadmap);
    $("s-stage-dots").replaceChildren(...((home.roadmap && home.roadmap.stages) || []).map((stage) =>
      el("span", { class: `dot st-${stage.status}`, title: `${stage.id} ${stage.title}: ${stage.plain_status}` })));
    if (home.next_stage) {
      $("s-next").textContent = `Next on the roadmap: ${home.next_stage.id} — ${home.next_stage.title}.`;
      $("s-next-why").textContent = `Status in the roadmap: ${home.next_stage.plain_status}` + (home.skipped && home.skipped.length ? ` · skipped ${home.skipped.map((item) => item.stage).join(", ")} (another agent has unfinished work there)` : "");
    } else {
      $("s-next").textContent = home.roadmap ? "The roadmap has no eligible stage left; type a task instead." : "No roadmap found for this repository; type a task.";
      $("s-next-why").textContent = "";
    }
    const campaign = home.campaign || {};
    $("until-done").checked = storageGet("agent-os-until-done", "0") === "1";
    const control = core.controls(home);
    S.control = control;
    if (!S.pending) {
      $("continue-button").disabled = !control.continueEnabled && !$("task-goal").value.trim();
      updateStartLabel();
      $("continue-spinner").classList.toggle("hidden", !control.busy);
    }
    renderOlder(home.older_runs || []);
    $("pause-button").disabled = !control.pauseEnabled;
    $("stop-button").disabled = !control.stopEnabled;
    $("resume-button").classList.toggle("hidden", !control.showResume);
    if (home.prep && home.prep.state === "running") renderPrep(home.prep);
    else if (S.shownRunId) api(`runs/${encodeURIComponent(S.shownRunId)}/simple`).then(renderRun).catch(() => { S.shownRunId = null; });
    else if (home.current_run) renderRun(home.current_run);
    else $("run-panel").classList.toggle("hidden", !(S.prep && S.prep.state !== "done"));
    if (campaign.status && campaign.stop_reason && campaign.status !== "active" && home.current_run && home.current_run.overall === "DONE") {
      $("r-headline").textContent = `Finished. ${campaign.stop_reason}`;
    }
  }

  function updateStartLabel() {
    if (S.pending) return;
    const typed = $("task-goal").value.trim();
    const control = S.control || {};
    $("continue-label").textContent = typed ? "START THIS TASK" : (control.continueLabel === "CONTINUE ROADMAP" ? "START (continue the roadmap)" : control.continueLabel || "START");
    $("continue-button").disabled = !typed && control.continueEnabled === false;
  }

  function renderOlder(runs) {
    $("older-runs-panel").classList.toggle("hidden", !runs.length);
    $("older-count").textContent = runs.length ? String(runs.length) : "";
    $("older-rows").replaceChildren(...runs.map((run) => el("tr", {},
      el("td", {}, (run.stage ? `${run.stage}: ` : "") + (run.goal || run.run_id).slice(0, 110)),
      el("td", { class: "muted" }, `${String(run.state || "").toLowerCase().replaceAll("_", " ")} · ${whenText(run.updated_at)}`),
      el("td", {},
        el("button", { class: "small", onclick: () => { S.shownRunId = run.run_id; loadHome(); $("run-panel").scrollIntoView({ behavior: "smooth" }); } }, "Show"),
        " ",
        el("button", { class: "small ghost", onclick: (event) => act(event.currentTarget, "stop", "dismissing the run", async () => {
          await api(`runs/${encodeURIComponent(run.run_id)}/dismiss`, {});
          if (S.shownRunId === run.run_id) S.shownRunId = null;
          await loadHome();
        }) }, "Dismiss")))));
  }

  // The quick Foreman picker: subscription foremen switch in one click; the
  // other sources (OpenRouter, local, Hugging Face GPU) live under More.
  async function quickForeman(select) {
    const choice = select.value;
    if (choice === "more" || choice === "registered") {
      $("more").open = true;
      $("foreman-panel").open = true;
      if (choice === "registered") {
        $("fm-source").value = "registered";
        S.foremanSourceSet = true;
        showSource();
      }
      $("foreman-panel").scrollIntoView({ behavior: "smooth" });
      await syncQuickForeman();
      return;
    }
    await act(null, "start-task", choice ? `making ${choice === "claude" ? "Claude" : "ChatGPT"} the foreman` : "switching back to the default planner", async () => {
      const view = choice ? await api("foreman/use", { kind: choice }) : await api("foreman/stop", {});
      renderForeman(view);
      toast(choice ? `${choice === "claude" ? "Claude" : "ChatGPT"} will plan the next runs` : "The default planner will plan the next runs");
    });
    await syncQuickForeman();
  }

  async function syncQuickForeman(view) {
    try {
      view = view || await api("foreman");
    } catch { return; }
    const live = FOREMAN_ACTIVE.includes(view.status);
    const select = $("quick-foreman");
    select.value = !live ? "" : ["claude", "chatgpt", "registered"].includes(view.kind) ? view.kind : "more";
    select.title = live ? `Foreman: ${SOURCE_LABEL[view.kind] || view.kind} (${(view.model || {}).repo || ""})` : "Default planner";
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
    $("r-tasks").textContent = view.tasks.total ? `(${view.tasks.done} of ${view.tasks.total} tasks done)` : "(planning…)";
    $("r-progress-bar").style.width = view.tasks.total ? `${Math.round(100 * view.tasks.done / view.tasks.total)}%` : "4%";
    $("r-steps").replaceChildren(...view.steps.map(stepItem));
    $("r-agents").replaceChildren(...view.agents.map((row) => el("tr", {},
      el("th", {}, row.agent), el("td", { class: `agent-${row.status.toLowerCase().replaceAll(" ", "-")}` }, row.status), el("td", { class: "muted" }, row.detail || ""))));
    $("r-warning").classList.toggle("hidden", !view.telemetry_warning);
    $("r-warning").textContent = view.telemetry_warning ? `Note: ${view.telemetry_warning}` : "";
    $("r-problems").replaceChildren(...view.problems.map(problemCard));
    const activity = $("r-activity");
    activity.replaceChildren(...view.activity.slice(-40).reverse().map((item) => el("li", {},
      el("span", { class: "t" }, new Date(item.at).toLocaleTimeString()), " — ", item.text)));
    renderSwarm(view.swarm);
    renderTaskList(view.task_list || []);
    renderUpdates(view.updates || []);
    renderChat(view);
    renderEfficiency(view.efficiency);
    renderSummary(view.summary);
    $("r-advanced").textContent = JSON.stringify({ run_id: view.run_id, advice: view.advice, efficiency_files: view.efficiency && view.efficiency.report.files }, null, 2);
  }

  // ------------------------------------------------------------ swarm, tasks, updates, chat

  function elapsed(iso) {
    if (!iso) return "";
    const seconds = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
    return seconds < 90 ? `${seconds}s` : seconds < 5400 ? `${Math.round(seconds / 60)} min` : `${(seconds / 3600).toFixed(1)} h`;
  }

  function renderSwarm(swarm) {
    swarm = swarm || { running: 0, by_model: {}, agents: [] };
    $("r-swarm-count").textContent = swarm.running ? `${swarm.running} agent${swarm.running === 1 ? "" : "s"} working` : "no agent working right now";
    $("r-swarm-models").textContent = Object.entries(swarm.by_model || {}).map(([model, count]) => `${model} ×${count}`).join(" · ");
    $("r-swarm-agents").replaceChildren(...swarm.agents.map((agent) => el("div", { class: "agent-card" },
      el("div", { class: "agent-top" },
        el("span", { class: "agent-model" }, [agent.provider, agent.model].filter(Boolean).join(" ") || "—"),
        el("span", { class: "muted" }, `${agent.phase} · ${elapsed(agent.since)}${agent.attempt > 1 ? ` · attempt ${agent.attempt}` : ""}`)),
      el("div", {}, el("b", {}, agent.task), ` — ${agent.doing}`),
      el("div", { class: "muted agent-goal" }, agent.goal))));
  }

  function renderTaskList(tasks) {
    $("r-tasklist").replaceChildren(...(tasks.length ? tasks.map((task) => el("div", { class: `task-row${task.failed ? " failed" : ""}` },
      el("div", { class: "task-top" },
        el("span", { class: "task-name", title: task.goal }, task.task),
        el("span", { class: "muted" }, `${task.status}${task.attempts > 1 ? ` · ${task.attempts} attempts` : ""}${task.model ? ` · ${task.model}` : ""}`)),
      el("div", { class: "progress small" }, el("div", { class: "progress-bar", style: `width:${Math.max(task.progress, 2)}%` }))))
      : [el("div", { class: "muted" }, "The foreman is planning the tasks…")]));
  }

  function renderUpdates(updates) {
    $("r-updates").replaceChildren(...(updates.length ? updates.map((item) => el("li", { class: item.needs_you ? "needs-you" : "" },
      el("span", { class: "t" }, new Date(item.at).toLocaleTimeString()), " ", item.text))
      : [el("li", { class: "muted" }, "No updates yet.")]));
  }

  function renderChat(view) {
    S.chatRunId = view.run_id;
    const open = view.questions_open || 0;
    $("chat-badge").classList.toggle("hidden", !open);
    $("chat-badge").textContent = open ? `${open} question${open === 1 ? "" : "s"}` : "";
    const log = $("chat-log");
    const typing = log.contains(document.activeElement);
    if (typing) return; // do not replace a reply box the user is typing in
    log.replaceChildren(...((view.chat || []).length ? view.chat.map((item) => el("div", { class: `bubble ${item.from}` },
      el("div", { class: "bubble-meta" }, `${item.from === "agent" ? `Agent (${item.task || "run"})` : "You"} · ${item.at ? new Date(item.at).toLocaleTimeString() : ""}`),
      el("div", {}, item.text),
      item.from === "agent" && item.open ? answerBox(view.run_id, item) : null))
      : [el("div", { class: "muted" }, "No questions from the agents yet. You can message them below.")]));
  }

  function answerBox(runId, item) {
    const input = el("input", { placeholder: "Your answer (the task continues with it)", autocomplete: "off" });
    const send = el("button", { class: "primary small", onclick: (event) => act(event.currentTarget, "resume", "sending your answer", async () => {
      await api(`runs/${encodeURIComponent(runId)}/decide`, { gate_id: item.gate_id, approve: true, note: input.value.trim() || undefined });
      await loadHome();
    }) }, "Answer");
    return el("div", { class: "chat-compose" }, input, send);
  }

  function showTab(name) {
    const chat = name === "chat";
    $("tab-chat").classList.toggle("on", chat);
    $("tab-updates").classList.toggle("on", !chat);
    $("tab-chat").setAttribute("aria-selected", String(chat));
    $("tab-updates").setAttribute("aria-selected", String(!chat));
    $("r-chat").classList.toggle("hidden", !chat);
    $("r-updates").classList.toggle("hidden", chat);
    storageSet("agent-os-run-tab", name);
  }

  async function sendChat(button) {
    const text = $("chat-input").value.trim();
    const runId = S.shownRunId || S.chatRunId;
    if (!text || !runId) return;
    await act(button, "resume", "sending your message", async () => {
      await api(`runs/${encodeURIComponent(runId)}/message`, { text });
      $("chat-input").value = "";
      await loadHome();
    });
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
    S.shownRunId = null;
    const untilDone = $("until-done").checked;
    // Immediate, local acknowledgement: the run panel appears with steps.
    S.prep = core.optimisticPrep();
    renderPrep(S.prep);
    await act(button, "continue", "starting the roadmap run", async () => {
      const result = await api("roadmap/continue", { project: S.project, repository: S.repository || undefined, auto_until_done: untilDone, preference: storageGet("agent-os-preference", "") || null, allow_paid_spend: $("allow-paid").checked });
      S.prep = result.prep;
      renderPrep(result.prep);
      pollPrep(result.prep.id);
    });
    // Keep the "Starting…" state until the preparation reports back.
    $("continue-button").disabled = true;
    $("continue-label").textContent = "Starting…";
  }

  async function runControl(button, action) {
    const runId = S.shownRunId || (S.home && S.home.current_run && S.home.current_run.run_id);
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

  function renderModels(view) {
    $("models-headline").textContent = view.headline + (view.source_problems.length ? ` · could not read: ${view.source_problems.join("; ")}` : "");
    const busy = view.jobs && Object.values(view.jobs).some((job) => job.state === "running");
    const open = view.proposal_cards.length;
    $("models-badge").classList.toggle("hidden", !open);
    $("models-badge").textContent = open ? `${open} suggestion${open > 1 ? "s" : ""}` : "";
    $("models-proposals").replaceChildren(...view.proposal_cards.map((card) => el("div", { class: "problem" },
      el("div", { class: "problem-title" }, card.title),
      el("p", {}, card.what),
      card.tried ? el("p", { class: "unchanged" }, card.tried) : null,
      el("p", { class: "muted" }, card.note),
      el("div", { class: "row" },
        el("button", { disabled: busy ? "disabled" : null, onclick: (event) => act(event.currentTarget, "retry", "trying the model on a small task", async () => renderModels(await api("models/trial", { provider: card.provider, model: card.candidate, tier: card.tier }))) }, "Try It First"),
        el("button", { class: "primary", onclick: (event) => act(event.currentTarget, "decide", "switching the model", async () => renderModels(await api("models/proposal", { id: card.id, decision: "apply" }))) }, "Use It"),
        el("button", { class: "ghost", onclick: (event) => act(event.currentTarget, "decide", "dismissing", async () => renderModels(await api("models/proposal", { id: card.id, decision: "dismiss" }))) }, "Not Now")))));
    $("models-tiers").replaceChildren(...view.tiers.map((row) => el("tr", {},
      el("td", {}, row.provider), el("td", {}, row.tier),
      el("td", {}, row.model + (row.runs_as && row.runs_as !== row.model ? ` (runs ${row.runs_as})` : "") + (row.overridden ? " · chosen by you" : "")),
      el("td", { class: row.outdated ? "wait" : "muted" }, row.outdated ? `vendor now says: ${row.description}` : (row.description || "")))));
    $("models-notices").replaceChildren(...(view.notices || []).slice(-5).reverse().map((notice) => el("div", { class: "muted" }, `${notice.at.slice(0, 10)} — ${notice.text}`)));
    $("models-scorecard").replaceChildren(...(view.scorecard || []).map((card) => el("tr", {},
      el("td", {}, `${card.provider}/${card.model}`), el("td", {}, card.role), el("td", { class: "num" }, card.calls),
      el("td", { class: "num" }, card.clean_rate === null ? "—" : `${Math.round(card.clean_rate * 100)}%`),
      el("td", { class: "num" }, core.formatNumber(card.mean_input_tokens)))));
    if (busy) setTimeout(() => api("models").then(renderModels).catch(() => {}), 3000);
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

  function rows(target, items, cells, empty) {
    const list = items || [];
    $(target).replaceChildren(...(list.length ? list.map((item) => el("tr", {}, ...cells(item).map((cell) => el("td", {}, cell == null ? "—" : String(cell)))))
      : [el("tr", {}, el("td", { class: "muted", colspan: "5" }, empty))]));
  }

  async function loadCompute() {
    const view = await api("model-compute");
    const b = view.budget || {};
    $("compute-note").textContent = (b.approved ? `Budget: $${b.remaining_usd} of $${b.project_usd} left · per-job cap $${b.job_hard_cap_usd}. ` : "No compute budget approved. ") + view.note;
    rows("compute-providers", view.providers, (p) => [p.id, (p.models || []).join(", "), p.deployment, p.refusal_profile, (p.roles || ["all"]).join(", ")], "No providers registered.");
    $("compute-catalog-size").textContent = view.catalog.size ? `(${view.catalog.size} in the local catalog)` : "";
    rows("compute-catalog", view.catalog.top, (m) => [m.model_id, m.pipeline, m.license, m.refusal_profile_hint, core.formatNumber(m.downloads)], "Nothing scanned yet: agent-os orchestrate radar scan");
    $("compute-inventory-at").textContent = view.inventory.fetched_at ? `(cached ${view.inventory.fetched_at.slice(0, 16).replace("T", " ")} UTC)` : "";
    rows("compute-inventory", view.inventory.offers, (o) => [o.name, `${o.vram_gb} GB`, o.tier, o.usd_per_hour.toFixed(2)], view.inventory.note || "No cached prices.");
    rows("compute-throughput", view.throughput, (t) => [t.model, t.gpu, t.engine, t.tokens_per_second, t.source], "No measurements yet: agent-os orchestrate throughput measure");
    const statuses = Object.entries(view.eval_queue.by_status || {}).map(([name, count]) => `${count} ${name}`).join(", ");
    $("compute-queue-summary").textContent = statuses ? `(${statuses})` : "";
    rows("compute-queue", view.eval_queue.recent, (q) => [q.model_id, q.status, (q.problems || [])[0] || q.reason || ""], "Queue is empty.");
    const signals = [
      ...Object.entries((view.refusals || {}).routes || {}).map(([route, r]) => [route, "refusals", `${r.total} (${Object.entries(r.categories).map(([k, v]) => `${k} ${v}`).join(", ")})`]),
      ...Object.entries(view.foreman || {}).map(([route, f]) => [route, "shadow foreman", `${f.proposals} proposals · agree ${f.agree} · cheaper ok ${f.cheaper_likely_ok} · cheaper risky ${f.cheaper_risky} · stronger ${f.stronger}`]),
    ];
    rows("compute-signals", signals, (s) => s, "No refusals or shadow proposals recorded.");
    const pending = (view.eval_queue.by_status || {}).queued || 0;
    $("compute-badge").classList.toggle("hidden", !pending);
    $("compute-badge").textContent = pending ? `${pending} to evaluate` : "";
  }

  // ------------------------------------------------------------ session foreman

  const FOREMAN_ACTIVE = ["planning", "provisioning", "loading", "ready"];
  const FOREMAN_LABEL = { planning: "sizing the model", provisioning: "renting a GPU", loading: "loading the model", ready: "live", stopped: "stopped", failed: "failed" };

  function money(value) { return value == null ? "—" : `$${Number(value).toFixed(2)}`; }

  const SOURCE_LABEL = { claude: "Claude", chatgpt: "ChatGPT", openrouter: "OpenRouter", local: "Local model", huggingface: "Hugging Face", registered: "Registered provider" };

  function showRegisteredModels() {
    const entry = (S.eligibleForemen || []).find((item) => item.provider === $("fm-reg-provider").value);
    const models = entry ? [...new Set(Object.values(entry.models || {}))] : [];
    $("fm-reg-model").replaceChildren(el("option", { value: "" }, entry ? `Default (${(entry.models || {}).reasoning || models[0] || entry.provider})` : "—"), ...models.map((m) => el("option", { value: m }, m)));
    $("fm-reg-note").textContent = entry
      ? [entry.adapter, entry.deployment, entry.billing, entry.paid ? "paid: only plans runs that allow paid credits" : "no outside spend"].filter(Boolean).join(" · ")
      : "No registered provider can be the foreman right now: it must be enabled, allowed to plan, and answering.";
    $("fm-use-reg").disabled = !entry;
  }

  async function loadEligibleForemen() {
    const { foremen } = await api("foreman/eligible");
    S.eligibleForemen = foremen || [];
    const current = $("fm-reg-provider").value;
    $("fm-reg-provider").replaceChildren(...(S.eligibleForemen.length
      ? S.eligibleForemen.map((item) => el("option", { value: item.provider }, `${item.provider}${item.paid ? " (paid)" : ""}`))
      : [el("option", { value: "" }, "(none eligible)")]));
    if (S.eligibleForemen.some((item) => item.provider === current)) $("fm-reg-provider").value = current;
    showRegisteredModels();
  }

  function showSource() {
    const source = $("fm-source").value;
    $("fm-sub").classList.toggle("hidden", !["claude", "chatgpt"].includes(source));
    $("fm-local").classList.toggle("hidden", source !== "local");
    $("fm-or").classList.toggle("hidden", source !== "openrouter");
    $("fm-reg").classList.toggle("hidden", source !== "registered");
    $("fm-hf").classList.toggle("hidden", source !== "huggingface");
    if (source === "registered" && !S.eligibleForemen) {
      S.eligibleForemen = [];
      loadEligibleForemen().catch((error) => { S.eligibleForemen = null; toast(error.message); });
    }
    const choice = (S.foremanChoices || {})[source];
    if (choice) {
      const current = $("fm-sub-model").value;
      $("fm-sub-model").replaceChildren(el("option", { value: "" }, `Default (${choice.default})`), ...choice.models.map((m) => el("option", { value: m }, m)));
      if (choice.models.includes(current)) $("fm-sub-model").value = current;
      $("fm-use").disabled = false;
    } else if (["claude", "chatgpt"].includes(source)) {
      $("fm-sub-model").replaceChildren(el("option", { value: "" }, "Not set up on this computer"));
      $("fm-use").disabled = true;
    }
    storageSet("agent-os-foreman-source", source);
  }

  function renderForeman(view) {
    S.foremanChoices = view.choices || {};
    syncQuickForeman(view);
    if (!S.foremanSourceSet) {
      S.foremanSourceSet = true;
      $("fm-source").value = FOREMAN_ACTIVE.includes(view.status) && view.kind ? view.kind : storageGet("agent-os-foreman-source", "claude");
    }
    showSource();
    $("fm-host").textContent = view.recommendation || "";
    $("fm-host").classList.toggle("hidden", !view.recommendation);
    const b = view.budget || {};
    if (document.activeElement !== $("fm-project") && $("fm-project").value === "" && b.project_usd != null) $("fm-project").value = b.project_usd;
    if (document.activeElement !== $("fm-job") && $("fm-job").value === "" && b.job_hard_cap_usd != null) $("fm-job").value = b.job_hard_cap_usd;
    $("fm-budget").textContent = b.approved ? `Budget left: ${money(b.remaining_usd)} of ${money(b.project_usd)}` : "No budget approved yet";
    const live = FOREMAN_ACTIVE.includes(view.status);
    $("fm-stop").classList.toggle("hidden", !live);
    $("foreman-badge").classList.toggle("hidden", !view.status);
    $("foreman-badge").textContent = view.status ? `${SOURCE_LABEL[view.kind] || ""} ${FOREMAN_LABEL[view.status] || view.status}`.trim() : "";
    if (!view.status) { $("fm-status").classList.add("hidden"); return live; }
    const model = view.model || {};
    const gpu = view.gpu || {};
    const facts = [
      ["Status", `${FOREMAN_LABEL[view.status] || view.status}${view.detail ? ` — ${view.detail}` : ""}`],
      ["Foreman", SOURCE_LABEL[view.kind] || view.kind],
      ["Model", model.repo ? `${model.repo}${model.sha ? ` @ ${model.sha.slice(0, 10)}` : ""}${model.params ? ` · ${(model.params / 1e9).toFixed(1)}B params` : ""}` : view.id],
      ["GPU", gpu.name ? `${gpu.gpu_count}× ${gpu.name} (${gpu.tier}) · ${money(view.hourly_usd || gpu.hourly_usd)}/hour` : null],
      ["Spent", view.kind === "huggingface" ? `${money(view.spent_usd)} of ${money(view.cap_usd)} job budget${view.minutes_left != null ? ` · shuts down in ≤ ${view.minutes_left} min` : ""}` : null],
      ["GPU use", view.utilization ? `${view.utilization.busy_pct}% busy over ${view.utilization.sampled_minutes} min · ${view.utilization.requests} requests · ${view.utilization.generation_tokens.toLocaleString()} tokens generated`
        + (view.utilization.usd_per_request != null ? ` · ${money(view.utilization.usd_per_request)}/request` : "")
        + (view.utilization.usd_per_mtok_generated != null ? ` · ${money(view.utilization.usd_per_mtok_generated)}/M tokens` : "")
        + ` · ${money(view.utilization.idle_usd)} spent idle` : null],
      ["Strategy", view.strategy ? `${view.strategy.band} planner (${view.strategy.source}) — ${view.strategy.summary}` : null],
      ["Backups", (view.backups || []).length ? view.backups.map((b) => SOURCE_LABEL[b.kind] || b.provider).join(" → ") + " (take over if the foreman hits its usage limit)" : null],
      ["Planner for", view.provider_id ? `${(view.runs || []).length} run(s) · provider ${view.provider_id}` : `${(view.runs || []).length} run(s) waiting`],
    ].filter(([, value]) => value);
    $("fm-status").replaceChildren(...facts.flatMap(([key, value]) => [el("dt", {}, key), el("dd", {}, value)]));
    $("fm-status").classList.remove("hidden");
    return live;
  }

  let foremanTimer = null;
  async function loadForeman() {
    const view = await api("foreman");
    const live = renderForeman(view);
    clearTimeout(foremanTimer);
    // only a rented GPU changes on its own (loading, spend, shutdown)
    if (live && view.kind === "huggingface") foremanTimer = setTimeout(() => loadForeman().catch(() => {}), 10000);
    return live;
  }

  function foremanInputs() {
    const link = $("fm-link").value.trim();
    const job = parseFloat($("fm-job").value);
    const project = parseFloat($("fm-project").value);
    if (!link) throw new Error("paste a Hugging Face model link first");
    if (!(job > 0)) throw new Error("set a budget for this job");
    if (!(project >= job)) throw new Error("the project budget must be at least the job budget");
    return { link, job_usd: job, project_usd: project, idle_minutes: parseInt($("fm-idle").value, 10) || 15 };
  }

  async function previewForeman() {
    const body = foremanInputs();
    const plan = await api("foreman/preview", body);
    const model = plan.model || {};
    const facts = [["Model", `${model.repo}${model.params ? ` · ${(model.params / 1e9).toFixed(1)}B params` : ""} · ${model.weight_gb} GB weights${model.gated ? " · gated" : ""}`],
      ["Needs", `${plan.vram_needed_gb ?? "?"} GB GPU memory · context ${plan.context ?? "?"} tokens`]];
    if (plan.error) facts.push(["Problem", plan.error]);
    else {
      const c = plan.choice;
      facts.push(["Would rent", `${c.gpu_count}× ${c.name} (${c.tier}) at ${money(c.hourly_usd)}/hour`]);
      facts.push(["Runs up to", `${c.max_hours} hours within ${money(body.job_usd)}, then shuts down`]);
      const alt = (plan.api_alternatives || [])[0];
      if (alt) facts.push(["Per-token instead", `${alt.id} (${alt.match}): $${alt.usd_per_plan.toFixed(5)} per plan on OpenRouter, no rental`]);
      if (plan.rent_or_api) facts.push(["Advice", plan.rent_or_api.advice]);
    }
    $("fm-status").replaceChildren(...facts.flatMap(([key, value]) => [el("dt", {}, key), el("dd", {}, value)]));
    $("fm-status").classList.remove("hidden");
  }

  function useForeman(button, body) {
    return act(button, "start-task", `switching the foreman to ${SOURCE_LABEL[body.kind]}`, async () => {
      renderForeman(await api("foreman/use", body));
    });
  }

  function wireForeman() {
    $("fm-source").addEventListener("change", showSource);
    $("fm-use").addEventListener("click", (event) => useForeman(event.currentTarget, { kind: $("fm-source").value, model: $("fm-sub-model").value || undefined }));
    $("fm-local-list").addEventListener("click", (event) => act(event.currentTarget, "refresh", "asking your local server for its models", async () => {
      const { models } = await api("foreman/local-models", { base_url: $("fm-local-url").value.trim() });
      $("fm-local-model").replaceChildren(...(models.length ? models.map((m) => el("option", { value: m }, m)) : [el("option", { value: "" }, "(no models loaded)")]));
    }));
    $("fm-or-load").addEventListener("click", (event) => act(event.currentTarget, "refresh", "reading OpenRouter's model list and prices", async () => {
      const { models } = await api("foreman/openrouter-models", {});
      $("fm-or-list").replaceChildren(...models.map((m) => el("option", { value: m.id }, `$${m.usd_per_mtok_in}/M in · $${m.usd_per_mtok_out}/M out · ${Math.round((m.context || 0) / 1000)}k ctx`)));
      toast(`${models.length} OpenRouter models listed, cheapest first`);
    }));
    $("fm-use-or").addEventListener("click", (event) => useForeman(event.currentTarget, { kind: "openrouter", model: $("fm-or-model").value.trim() }));
    $("fm-use-local").addEventListener("click", (event) => useForeman(event.currentTarget, { kind: "local", base_url: $("fm-local-url").value.trim(), model: $("fm-local-model").value || undefined }));
    $("fm-reg-provider").addEventListener("change", showRegisteredModels);
    $("fm-use-reg").addEventListener("click", (event) => useForeman(event.currentTarget, { kind: "registered", provider: $("fm-reg-provider").value, model: $("fm-reg-model").value || undefined }));
    $("foreman-panel").addEventListener("toggle", (event) => { if (event.target.open) { S.eligibleForemen = null; act(null, "refresh", "reading the session foreman", loadForeman); } });
    $("fm-preview").addEventListener("click", (event) => act(event.currentTarget, "refresh", "reading the model and GPU prices", previewForeman));
    $("fm-deploy").addEventListener("click", (event) => act(event.currentTarget, "start-task", "starting the foreman deployment", async () => {
      renderForeman(await api("foreman/deploy", foremanInputs()));
      await loadForeman();
    }));
    $("fm-stop").addEventListener("click", (event) => act(event.currentTarget, "stop", "shutting the foreman GPU down", async () => {
      renderForeman(await api("foreman/stop", {}));
    }));
    loadForeman().then((live) => { if (live) $("foreman-panel").open = true; }).catch(() => {});
  }

  // ------------------------------------------------------------ model services

  const SERVICE_STATUS = { preset_ready: "ready to add", preset_restricted: "add after reading the terms", bridge_claude_code: "Claude Code bridge",
    catalog_only: "listed only", deferred: "not yet" };
  const SERVICE_ADDABLE = ["preset_ready", "preset_restricted"];
  const BRIDGE_ALIAS = { fast: "haiku", balanced: "sonnet", reasoning: "opus" };

  function planText(plan) {
    const billing = plan.billing || {};
    const price = plan.usd_per_month != null ? ` · $${plan.usd_per_month}/month` : "";
    const terms = plan.allowance_summary || [billing.mode, billing.overage ? `overage ${billing.overage}` : null].filter(Boolean).join(", ") || "billing unknown";
    return `${plan.name || plan.id}: ${terms}${price}`;
  }

  function restrictionText(item) {
    const r = item.restrictions || {};
    const notes = [r.notes, (r.disallowed_uses || []).length ? `not for ${r.disallowed_uses.join(", ")}` : null];
    if (!SERVICE_ADDABLE.includes(item.integration_status) && item.integration_status !== "bridge_claude_code") notes.unshift(item.integration_notes);
    return notes.filter(Boolean).join(" · ") || "—";
  }

  function privacyText(privacy) {
    const p = privacy || {};
    const zdr = p.zdr == null ? "unknown" : p.zdr ? "yes" : "no";
    return `training: ${p.training_on_prompts ?? "unknown"} · ZDR: ${zdr}`;
  }

  function renderServices(view) {
    S.services = view.services || [];
    $("services-badge").classList.toggle("hidden", !(view.notice || view.warnings || view.errors));
    $("services-badge").textContent = view.notice ? "not compiled" : view.errors ? `${view.errors} errors` : view.warnings ? `${view.warnings} warnings` : "";
    if (view.notice) {
      $("services-list").replaceChildren(el("tr", {}, el("td", { colspan: "6", class: "muted" }, `The model service ${view.notice}. It appears here once it is compiled.`)));
      return;
    }
    $("services-list").replaceChildren(...(S.services.length ? S.services.flatMap((item) => {
      const open = S.serviceOpen === item.id;
      const row = el("tr", { class: `svc-row${open ? " open" : ""}`, title: "Show endpoints and add it", onclick: () => toggleService(item.id) },
        el("td", {}, item.name || item.id, item.stale ? el("span", { class: "badge stale", title: `reviewed ${item.reviewed_at || "never"}; check the vendor's current terms` }, "stale") : null),
        el("td", {}, (item.category || "").replace(/_/g, " ")),
        el("td", {}, SERVICE_STATUS[item.integration_status] || item.integration_status || ""),
        el("td", {}, ...(item.plans || []).map((plan) => el("div", {}, planText(plan)))),
        el("td", {}, restrictionText(item)),
        el("td", {}, privacyText(item.privacy)));
      return open ? [row, el("tr", { class: "svc-detail" }, el("td", { colspan: "6" }, serviceDetail(item)))] : [row];
    }) : [el("tr", {}, el("td", { colspan: "6", class: "muted" }, "The catalog lists no services."))]));
  }

  function toggleService(id) {
    S.serviceOpen = S.serviceOpen === id ? null : id;
    renderServices({ services: S.services });
  }

  function serviceDetail(item) {
    const plans = item.plans || [];
    const bridge = item.integration_status === "bridge_claude_code";
    const firstPlan = (bridge && plans.find((plan) => (plan.allowed_clients || []).some((c) => /claude code/i.test(c)))) || plans[0];
    const endpoint = el("select", {}, ...(item.endpoints || []).map((ep) => el("option", { value: ep.id }, `${ep.id} (${ep.protocol})`)));
    const plan = el("select", {}, ...plans.map((p) => el("option", { value: p.id }, p.name || p.id)));
    const model = el("select", {}, el("option", { value: "" }, "(press List models)"));
    const classes = ["fast", "balanced", "reasoning"].map((name) => el("input", { type: "checkbox", value: name }));
    classes.forEach((box) => { box.checked = box.value !== "reasoning"; });
    const ack = el("input", { type: "checkbox" });
    const ackLabel = el("label", { class: "inline switch" }, ack, " I have read this plan's terms");
    const result = el("pre", { class: "svc-result hidden" });
    const chosenPlan = () => plans.find((p) => p.id === plan.value);
    const syncPlan = () => {
      const current = chosenPlan();
      ackLabel.classList.toggle("hidden", !(current && current.needs_ack));
      if (current && current.endpoint && (item.endpoints || []).some((ep) => ep.id === current.endpoint) && !bridge) endpoint.value = current.endpoint;
    };
    if (firstPlan) plan.value = firstPlan.id;
    plan.addEventListener("change", syncPlan);
    syncPlan();
    const fillModels = (ids) => {
      const current = model.value;
      model.replaceChildren(el("option", { value: "" }, ids.length ? "(choose a model)" : "(no models listed)"), ...ids.map((id) => el("option", { value: id }, id)));
      if (ids.includes(current)) model.value = current;
    };
    // The catalog's own model list (local; no vendor call) until List models asks the vendor.
    api(`services/${encodeURIComponent(item.id)}`).then((detail) => {
      if (model.options.length <= 1) fillModels((detail.models || []).map((m) => m.id).filter(Boolean));
    }).catch(() => {});
    const body = (write) => {
      const picked = classes.filter((box) => box.checked).map((box) => box.value);
      const base = { service: item.id, plan: plan.value || undefined, ack_terms: ack.checked, write };
      // A bridge maps the chosen model onto Claude Code's alias for each ticked work type.
      if (bridge) return { ...base, models: model.value ? Object.fromEntries(picked.map((name) => [BRIDGE_ALIAS[name], model.value])) : undefined };
      if (!model.value) throw new Error("pick a model (List models asks the service for its list)");
      if (!picked.length) throw new Error("pick at least one work type");
      return { ...base, model: model.value, classes: picked, endpoint: endpoint.value || undefined };
    };
    const send = async (write) => {
      const view = await api(bridge ? "services/bridge" : "services/add", body(write));
      result.textContent = view.error || JSON.stringify(view.entry || view, null, 2);
      result.classList.remove("hidden");
      if (view.written) {
        toast(`${(view.entry || {}).id || "provider"} added to your providers`);
        S.eligibleForemen = null;
      }
    };
    const actions = [];
    if (SERVICE_ADDABLE.includes(item.integration_status) || bridge) {
      actions.push(el("button", { onclick: (event) => act(event.currentTarget, "refresh", "previewing the provider entry", () => send(false)) }, "Preview"));
      actions.push(el("button", { class: "primary", onclick: (event) => act(event.currentTarget, "start-task", "adding the provider", () => send(true)) },
        bridge ? "Add as Claude Code bridge" : "Add to my providers"));
    } else {
      actions.push(el("span", { class: "muted" }, `Not addable: ${item.integration_notes || SERVICE_STATUS[item.integration_status] || item.integration_status}`));
    }
    return el("div", { class: "svc-panel" },
      el("ul", { class: "svc-endpoints" }, ...(item.endpoints || []).map((ep) => el("li", {}, `${ep.id} · ${ep.protocol} · `, el("code", {}, ep.base_url || "")))),
      el("div", { class: "row" },
        el("label", {}, "Endpoint", endpoint),
        el("button", { onclick: (event) => act(event.currentTarget, "refresh", `asking ${item.name || item.id} for its models`, async () => {
          const { models } = await api("services/discover", { service: item.id, endpoint: endpoint.value || undefined });
          fillModels(models || []);
          toast(`${(models || []).length} model${(models || []).length === 1 ? "" : "s"} listed`);
        }) }, "List models")),
      el("div", { class: "row" },
        plans.length ? el("label", {}, "Plan", plan) : null,
        el("label", {}, "Model", model)),
      el("div", { class: "row" }, ...classes.map((box) => el("label", { class: "inline switch" }, box, ` ${box.value}`)), ackLabel),
      el("div", { class: "row" }, ...actions),
      result);
  }

  async function loadServices() {
    renderServices(await api("services"));
  }

  function wireSimple() {
    wireForeman();
    $("services-panel").addEventListener("toggle", (event) => { if (event.target.open) act(null, "refresh", "reading the model service catalog", loadServices); });
    $("compute-panel").addEventListener("toggle", (event) => { if (event.target.open) act(null, "refresh", "reading models and compute", loadCompute); });
    $("models-panel").addEventListener("toggle", (event) => { if (event.target.open) act(null, "refresh", "reading the model list", async () => renderModels(await api("models"))); });
    $("models-refresh").addEventListener("click", (event) => act(event.currentTarget, "refresh", "checking the official model lists", async () => renderModels(await api("models/refresh", {}))));
    $("usage-panel").addEventListener("toggle", (event) => { if (event.target.open) act(null, "refresh", "adding up model usage", loadUsage); });
    // One Start button: a typed task starts that task; an empty box continues the roadmap.
    $("continue-button").addEventListener("click", (event) => {
      const goal = $("task-goal").value.trim();
      if (!goal) { continueRoadmap(event.currentTarget); return; }
      act(event.currentTarget, "start-task", "starting your task", async () => {
        await api("runs", { goal, project: S.project, repository: S.repository || undefined, start_recommended: true, auto_continue: true, preference: storageGet("agent-os-preference", "") || undefined, allow_paid_spend: $("allow-paid").checked });
        $("task-goal").value = "";
        S.shownRunId = null;
        updateStartLabel();
        await loadHome();
      });
    });
    $("task-goal").addEventListener("input", updateStartLabel);
    $("tab-updates").addEventListener("click", () => showTab("updates"));
    $("tab-chat").addEventListener("click", () => showTab("chat"));
    showTab(storageGet("agent-os-run-tab", "updates"));
    $("chat-send").addEventListener("click", (event) => sendChat(event.currentTarget));
    $("chat-input").addEventListener("keydown", (event) => { if (event.key === "Enter") sendChat($("chat-send")); });
    $("quick-foreman").addEventListener("change", (event) => quickForeman(event.currentTarget));
    $("help-button").addEventListener("click", (event) => tellMeWhatToPress(event.currentTarget));
    $("advice-close").addEventListener("click", () => $("advice").classList.add("hidden"));
    $("pause-button").addEventListener("click", (event) => runControl(event.currentTarget, "pause"));
    $("resume-button").addEventListener("click", (event) => runControl(event.currentTarget, "resume"));
    $("stop-button").addEventListener("click", (event) => runControl(event.currentTarget, "stop"));
    $("until-done").addEventListener("change", (event) => storageSet("agent-os-until-done", event.target.checked ? "1" : "0"));
    $("allow-paid").checked = storageGet("agent-os-allow-paid", "0") === "1";
    $("allow-paid").addEventListener("change", (event) => storageSet("agent-os-allow-paid", event.target.checked ? "1" : "0"));
    $("settings-button").addEventListener("click", () => { $("set-preference").value = storageGet("agent-os-preference", "balanced"); $("settings-dialog").showModal(); });
    $("settings-close").addEventListener("click", () => { storageSet("agent-os-preference", $("set-preference").value); $("settings-dialog").close(); });
    $("explain-close").addEventListener("click", () => $("explain-dialog").close());
    $("repo-button").addEventListener("click", openRepos);
    $("repo-close").addEventListener("click", () => $("repo-dialog").close());
    $("repo-search").addEventListener("input", renderRepos);
    $("repo-new-button").addEventListener("click", () => { $("repo-new").classList.toggle("hidden"); $("repo-new-name").focus(); });
    $("repo-new-cancel").addEventListener("click", () => $("repo-new").classList.add("hidden"));
    $("repo-new-create").addEventListener("click", (event) => createRepo(event.currentTarget));
    $("mode-simple").addEventListener("click", () => setMode("simple"));
    $("mode-advanced").addEventListener("click", () => setMode("advanced"));
  }

  // ------------------------------------------------------------ repositories

  function whenText(iso) {
    if (!iso) return "no commits yet";
    const days = Math.floor((Date.now() - Date.parse(iso)) / 86400000);
    if (days <= 0) return "changed today";
    if (days === 1) return "changed yesterday";
    if (days < 60) return `changed ${days} days ago`;
    return `changed ${new Date(iso).toLocaleDateString()}`;
  }

  async function openRepos() {
    if (!$("repo-dialog").open) $("repo-dialog").showModal();
    $("repo-search").value = "";
    try {
      const data = await api("repos");
      S.repos = data.repositories || [];
      $("repo-new-parent").replaceChildren(...(data.roots || []).map((root) => el("option", { value: root }, root)));
      $("repo-roots").textContent = data.roots && data.roots.length ? `Looked in ${data.roots.join(", ")}` : "";
      renderRepos();
      $("repo-search").focus();
    } catch (error) {
      $("repo-list").replaceChildren(el("p", { class: "muted" }, `Could not list repositories: ${error.message}`));
    }
  }

  function renderRepos() {
    const needle = $("repo-search").value.trim().toLowerCase();
    const current = S.home ? String(S.home.repository || "").toLowerCase() : "";
    const shown = S.repos.filter((repo) => !needle || `${repo.name} ${repo.project || ""} ${repo.path}`.toLowerCase().includes(needle));
    if (!shown.length) {
      $("repo-list").replaceChildren(el("p", { class: "muted" }, needle ? "No repository matches that search." : "No repositories found. Press + New repository to make one."));
      return;
    }
    $("repo-list").replaceChildren(...shown.map((repo) => el("button", {
      class: `repo-card${repo.path.toLowerCase() === current ? " current" : ""}`, role: "listitem", type: "button",
      disabled: repo.git ? undefined : "disabled",
      title: repo.git ? `Work in ${repo.path}` : "This folder is not a Git repository yet, so agents cannot work in it safely.",
      onclick: () => chooseRepo(repo),
    },
      el("span", { class: "repo-title" }, repo.name,
        repo.project && repo.project !== repo.name ? el("span", { class: "badge" }, repo.project) : null,
        repo.branch && repo.branch !== "main" ? el("span", { class: "badge" }, repo.branch) : null,
        repo.git ? null : el("span", { class: "badge" }, "not a Git repository")),
      el("span", { class: "repo-when" }, repo.git ? whenText(repo.last_commit) : ""),
      el("span", { class: "repo-path" }, repo.path))));
  }

  function chooseRepo(repo) {
    if (!repo.git) return;
    S.project = repo.project || null;
    S.repository = repo.project ? null : repo.path;
    storageSet("agent-os-repo", JSON.stringify({ project: S.project, repository: S.repository }));
    if ($("repo-dialog").open) $("repo-dialog").close();
    $("repo-name").textContent = repo.name;
    act(null, "refresh", `opening ${repo.name}`, loadHome);
  }

  async function createRepo(button) {
    const name = $("repo-new-name").value.trim();
    if (!name) { $("repo-new-name").focus(); toast("Type a name for the new repository first."); return; }
    const github = $("repo-new-github").checked;
    await act(button, "create-repository", github ? "creating the repository and uploading it to GitHub" : "creating the repository", async () => {
      const created = await api("repos", { name, description: $("repo-new-description").value, parent: $("repo-new-parent").value || undefined, github });
      if (created.github && !created.github.ok) toast(`Created locally. GitHub: ${created.github.message}`);
      $("repo-new").classList.add("hidden");
      $("repo-new-name").value = "";
      $("repo-new-description").value = "";
      $("repo-new-github").checked = false;
      chooseRepo({ ...created, git: true, project: null });
    });
  }

  wireSimple();
  setMode(storageGet("agent-os-mode", "simple"));
  let remembered = null;
  try { remembered = JSON.parse(storageGet("agent-os-repo", "null")); } catch { remembered = null; }
  if (remembered) { S.project = remembered.project || null; S.repository = remembered.repository || null; }
  // First visit: show the list so the user picks where to work.
  act(null, "refresh", "reading the project and roadmap", loadHome).then((home) => { if (!remembered || !home) openRepos(); });

})();
