// Simple Mode UI state (gui/simple-core.js). Run: node --test tests/gui/
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const core = require("../../gui/simple-core.js");

test("every button acknowledges a click with new visible text", () => {
  for (const action of ["continue", "start-task", "pause", "stop", "resume", "decide", "retry", "fresh", "help"]) {
    const ack = core.acknowledge(action);
    assert.equal(ack.busy, true);
    assert.ok(ack.buttonLabel.length > 0, action);
    assert.ok(ack.status.endsWith("..."), `${action} says what it is doing`);
  }
  assert.equal(core.acknowledge("continue").status, "Starting roadmap run...");
  assert.equal(core.acknowledge("unknown-action").status, "Working...");
});

test("Continue Roadmap shows its steps before the server answers", () => {
  const prep = core.optimisticPrep();
  assert.equal(prep.state, "running");
  assert.equal(prep.steps[0].status, "active");
  assert.equal(prep.steps[0].label, "Reading repository");
  assert.ok(prep.steps.slice(1).every((step) => step.status === "pending"));
});

test("long waits explain themselves instead of a bare spinner", () => {
  assert.equal(core.stillWorking("starting the roadmap run", 300), null);
  assert.match(core.stillWorking("starting the roadmap run", 1200), /Still working: starting the roadmap run \(1s\)/);
  assert.match(core.stillWorking("x", 7000), /can take a little while/);
});

test("step icons distinguish done, active, waiting and failed", () => {
  const icons = ["done", "active", "pending", "waiting", "failed", "skipped"].map(core.stepIcon);
  assert.equal(new Set(icons).size, icons.length);
});

test("controls follow the run state", () => {
  const working = core.controls({ current_run: { overall: "WORKING" } });
  assert.equal(working.continueEnabled, false);
  assert.equal(working.pauseEnabled, true);
  assert.equal(working.continueLabel, "Working…");
  assert.equal(working.busy, true);
  assert.equal(core.controls({ current_run: { overall: "NEEDS YOU" } }).busy, false, "no spinner while waiting for the user");
  const paused = core.controls({ current_run: { overall: "PAUSED" } });
  assert.equal(paused.showResume, true);
  assert.equal(paused.continueEnabled, true);
  const preparing = core.controls({ prep: { state: "running" }, current_run: null });
  assert.equal(preparing.continueLabel, "Starting…");
  assert.equal(preparing.continueEnabled, false);
  const idle = core.controls({ current_run: null });
  assert.equal(idle.continueEnabled, true);
  assert.equal(idle.continueLabel, "CONTINUE ROADMAP");
  assert.equal(core.controls({ current_run: { overall: "NEEDS YOU" } }).continueEnabled, false);
});

test("advice targets map to real buttons", () => {
  assert.equal(core.adviceElementId("continue"), "continue-button");
  assert.equal(core.adviceElementId("resume"), "resume-button");
  assert.equal(core.adviceElementId("problem:G2"), "problem-G2-recommended");
  assert.equal(core.adviceElementId(null), null);
});

test("dashboard rows always carry an accuracy label and never fake a value", () => {
  const missing = core.effRow({ label: "Estimated tokens avoided", value: null, accuracy: "estimated" });
  assert.equal(missing.value, "not available");
  assert.equal(missing.accuracy, "estimated");
  assert.equal(core.effRow({ label: "x", value: 95.8, unit: "%", accuracy: "estimated" }).value, "95.8%");
  assert.equal(core.effRow({ label: "x", value: 82411, accuracy: "exact" }).value, "82,411");
});

test("roadmap line", () => {
  assert.equal(core.roadmapLine({ complete: 23, total: 34 }), "23 / 34 stages complete");
  assert.equal(core.roadmapLine(null), "No roadmap found");
});
