"use strict";
const {test} = require("node:test");
const assert = require("node:assert/strict");
const {screenMetadata, parseInputs} = require("../web/app.js");

function sample(overrides = {}) {
  return {
    task_id: "T1", target_identifier: "SAMPLE-1",
    primary_metric: 1, secondary_metric: 1, status_descriptor: "NOMINAL",
    is_critical_flag: false, ...overrides
  };
}

test("nominal metadata is routine", () => {
  const r = screenMetadata(sample());
  assert.equal(r.overall_urgency, "ROUTINE");
  assert.equal(r.total_alerts, 0);
});
test("strict thresholds match Python worker rules", () => {
  assert.equal(screenMetadata(sample({primary_metric: 25, secondary_metric: 12})).total_alerts, 0);
  const r = screenMetadata(sample({primary_metric: 25.1, secondary_metric: 12.1}));
  assert.equal(r.total_alerts, 2);
  assert.equal(r.overall_urgency, "ELEVATED_RISK");
});
test("critical flag escalates urgency", () => {
  const r = screenMetadata(sample({is_critical_flag: true}));
  assert.equal(r.overall_urgency, "CRITICAL_STAT_PANIC");
  assert.equal(r.critical_alerts_count, 1);
});
test("descriptor keywords match Python worker rules", () => {
  const r = screenMetadata(sample({status_descriptor: "discordant"}));
  assert.equal(r.total_alerts, 1);
});
test("missing measurement must not be parsed as zero", () => {
  const doc = {getElementById: id => ({
    task_id: {value: "T1"}, target_id: {value: "SAMPLE-1"},
    primary_metric: {value: ""}, secondary_metric: {value: "5"},
    status_descriptor: {value: "NOMINAL"}, is_critical: {checked: false}
  }[id])};
  assert.throws(() => parseInputs(doc), /finite numeric/);
});
