// Simple Mode: pure UI state helpers (no DOM). Loaded by the browser as a
// global and by Node for tests (tests/gui/simple_core.test.js).
"use strict";

(function (root) {
  // What the screen says the instant a button is pressed, before the server
  // has answered. The UI must never look unchanged after a click.
  const ACK = {
    continue: { button: "Starting…", status: "Starting roadmap run..." },
    "start-task": { button: "Starting…", status: "Starting your task..." },
    pause: { button: "Pausing…", status: "Pausing: no new work will start..." },
    stop: { button: "Stopping…", status: "Stopping the agents that are working..." },
    resume: { button: "Resuming…", status: "Resuming the run..." },
    decide: { button: "Sending…", status: "Sending your decision..." },
    retry: { button: "Retrying…", status: "Trying that part again..." },
    fresh: { button: "Starting…", status: "Setting the old run aside and starting fresh..." },
    help: { button: "Checking…", status: "Looking at what is happening right now..." },
    refresh: { button: "Loading…", status: "Loading..." },
    "create-repository": { button: "Creating…", status: "Creating the new repository..." },
  };

  const PREP_STEPS = [
    "Reading repository",
    "Checking roadmap",
    "Checking unfinished work",
    "Loading previous handoff",
    "Choosing the next task and agent",
    "Starting work",
  ];

  function acknowledge(action) {
    const ack = ACK[action] || { button: "Working…", status: "Working..." };
    return { busy: true, buttonLabel: ack.button, status: ack.status, startedAt: Date.now() };
  }

  // Shown immediately after Continue Roadmap is pressed, before the server
  // reports its first step.
  function optimisticPrep() {
    return {
      state: "running",
      message: ACK.continue.status,
      steps: PREP_STEPS.map((label, index) => ({ label, status: index === 0 ? "active" : "pending", detail: null })),
    };
  }

  function stillWorking(label, elapsedMs) {
    if (elapsedMs < 700) return null;
    const seconds = Math.round(elapsedMs / 1000);
    let text = `Still working: ${label}`;
    if (seconds >= 1) text += ` (${seconds}s)`;
    if (elapsedMs >= 6000) text += ". Starting an agent or scanning a large project can take a little while.";
    return text;
  }

  const ICONS = { done: "✓", active: "●", pending: "○", waiting: "!", failed: "✗", skipped: "–" };
  function stepIcon(status) { return ICONS[status] || "○"; }

  const OVERALL_CLASS = { WORKING: "working", "NEEDS YOU": "needs", PAUSED: "paused", STOPPED: "stopped", DONE: "done", READY: "ready", INTERRUPTED: "needs", STARTING: "working" };
  function overallClass(overall) { return OVERALL_CLASS[overall] || "ready"; }

  function formatNumber(value) {
    if (value === null || value === undefined) return "—";
    if (typeof value === "number") return value.toLocaleString("en-US", { maximumFractionDigits: 2 });
    return String(value);
  }

  // One dashboard row: value plus a visible accuracy label, never a bare estimate.
  function effRow(row) {
    const unit = row.unit === "%" ? "%" : row.unit ? ` ${row.unit}` : "";
    const value = row.value === null || row.value === undefined ? "not available" : formatNumber(row.value) + unit;
    return { label: row.label, value, accuracy: row.accuracy, help: row.help };
  }

  // Map an advice target to the element to highlight.
  const TARGETS = {
    continue: "continue-button", "start-task": "start-task-button", "view-progress": "view-progress-button",
    pause: "pause-button", resume: "resume-button", stop: "stop-button", settings: "settings-button",
  };
  function adviceElementId(target) {
    if (!target) return null;
    if (target.startsWith("problem:")) return `problem-${target.slice(8)}-recommended`;
    return TARGETS[target] || null;
  }

  // Which controls make sense in this state (disabled ones stay visible).
  function controls(home) {
    const run = home && home.current_run;
    const preparing = home && home.prep && home.prep.state === "running";
    const overall = run ? run.overall : null;
    const working = overall === "WORKING" || preparing;
    return {
      continueEnabled: !working && overall !== "NEEDS YOU",
      pauseEnabled: overall === "WORKING",
      stopEnabled: overall === "WORKING" || overall === "INTERRUPTED",
      showResume: overall === "PAUSED" || overall === "INTERRUPTED",
      busy: Boolean(working),
      continueLabel: preparing ? "Starting…" : working ? "Working…" : "CONTINUE ROADMAP",
    };
  }

  function roadmapLine(roadmap) {
    if (!roadmap) return "No roadmap found";
    return `${roadmap.complete} / ${roadmap.total} stages complete`;
  }

  const api = { ACK, PREP_STEPS, acknowledge, optimisticPrep, stillWorking, stepIcon, overallClass, formatNumber, effRow, adviceElementId, controls, roadmapLine };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.SimpleCore = api;
})(typeof window !== "undefined" ? window : globalThis);
