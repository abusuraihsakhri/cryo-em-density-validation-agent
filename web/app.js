"use strict";

// Browser implementation of the same illustrative rules in agents/workers.py.
// This is metadata screening, not Fourier shell correlation or density-map analysis.
function screenMetadata(input) {
  const alerts = [];
  function alert(origin, urgency, summary, detail) {
    alerts.push({origin_worker: origin, urgency, summary, technical_details: detail,
      actionable_remediation: "Review the underlying measurement and its intended interpretation."});
  }
  if (input.primary_metric > 25) {
    alert("InvariantQCWorker", "ELEVATED_RISK", "Primary metric threshold exceeded",
      "Primary metric " + input.primary_metric + " is greater than the illustrative threshold 25.");
  }
  if (input.is_critical_flag || input.secondary_metric > 12) {
    alert("SafetyEscalationWorker", input.is_critical_flag ? "CRITICAL_STAT_PANIC" : "ELEVATED_RISK",
      "Secondary/critical condition triggered",
      "Secondary metric " + input.secondary_metric + "; critical flag: " + input.is_critical_flag + ".");
  }
  if (["DISCORDANT", "ANOMALY", "MUTANT", "VIOLATION", "FAIL", "REJECT"]
      .some(term => input.status_descriptor.toUpperCase().includes(term))) {
    alert("ProtocolConformanceWorker", "ELEVATED_RISK", "Descriptor review flag",
      "The supplied descriptor contains a configured review keyword.");
  }
  const critical = alerts.filter(a => a.urgency === "CRITICAL_STAT_PANIC").length;
  const urgency = critical ? "CRITICAL_STAT_PANIC" : alerts.length ? "ELEVATED_RISK" : "ROUTINE";
  return {
    task_id: input.task_id,
    target_identifier: input.target_identifier,
    overall_urgency: urgency,
    integrity_status: critical ? "RECALIBRATION_REQUIRED" : alerts.length ? "DISCORDANT_ANOMALY" : "VALIDATED_OPTIMAL",
    total_alerts: alerts.length,
    critical_alerts_count: critical,
    alerts,
    computation: "Local browser rule evaluation; no HMAC or server audit log",
    disclaimer: "Illustrative metadata thresholds only. No FSC, local-resolution, or map-to-model calculation is performed."
  };
}

function parseInputs(doc) {
  const get = id => doc.getElementById(id);
  const p = get("primary_metric").value.trim();
  const s = get("secondary_metric").value.trim();
  if (!p || !s || !Number.isFinite(Number(p)) || !Number.isFinite(Number(s))) {
    throw new Error("Both measurements must be finite numeric values.");
  }
  const task = get("task_id").value.trim();
  const target = get("target_id").value.trim();
  if (!task || !target) throw new Error("Task and target identifiers are required.");
  return {
    task_id: task,
    target_identifier: target,
    primary_metric: Number(p),
    secondary_metric: Number(s),
    status_descriptor: get("status_descriptor").value.trim(),
    is_critical_flag: get("is_critical").checked
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {screenMetadata, parseInputs};
}

if (typeof document !== "undefined") {
  const get = id => document.getElementById(id);
  const form = get("audit-form");
  const output = get("result");
  const download = get("download");
  const button = get("run");
  let lastReport = null;
  let count = 0;

  form.addEventListener("submit", async event => {
    event.preventDefault();
    download.disabled = true;
    button.disabled = true;
    output.textContent = "Evaluating input…";
    try {
      const input = parseInputs(document);
      let data;
      if (get("server-mode").checked) {
        const response = await fetch("./api/audit", {
          method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(input)
        });
        if (!response.ok) {
          let details = "HTTP " + response.status;
          try {
            const body = await response.json();
            if (typeof body.detail === "string") details += ": " + body.detail;
          } catch (_) { /* response may not be JSON */ }
          throw new Error("API audit failed (" + details + "). No simulated result was substituted.");
        }
        data = await response.json();
      } else {
        data = screenMetadata(input);
      }
      lastReport = data;
      output.textContent = JSON.stringify(data, null, 2);
      get("status").textContent = data.overall_urgency;
      get("alerts").textContent = String(data.total_alerts);
      get("tasks").textContent = String(++count);
      download.disabled = false;
    } catch (err) {
      output.textContent = "Evaluation failed: " + err.message;
      get("status").textContent = "ERROR";
      lastReport = null;
    } finally {
      button.disabled = false;
    }
  });

  download.addEventListener("click", () => {
    if (!lastReport) return;
    const blob = new Blob([JSON.stringify(lastReport, null, 2) + "\n"], {type: "application/json"});
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "cryo-em-screening-report.json";
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  });
}
