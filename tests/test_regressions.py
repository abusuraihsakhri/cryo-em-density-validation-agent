"""Regression checks for CSV parsing, API privacy, and input validation."""
import csv
import os
import pytest
from pydantic import ValidationError

from agents.models import SystemTaskPayload
from agents.api import app
from cli import main as main_cli
from cryo_em_validator.cli import main as frontier_cli


@pytest.mark.parametrize("value", ["False", "false", "0", "no", ""])
def test_main_batch_false_is_not_critical(value, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with open("inputs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "task_id", "target_identifier", "primary_metric", "secondary_metric",
            "is_critical_flag", "status_descriptor"
        ])
        writer.writeheader()
        writer.writerow(dict(task_id="T1", target_identifier="SAMPLE-1",
                             primary_metric=1, secondary_metric=1,
                             is_critical_flag=value, status_descriptor="NOMINAL"))
    assert main_cli(["batch", "-i", "inputs.csv", "-o", "outputs.csv"]) == 0
    with open("outputs.csv", encoding="utf-8") as f:
        row = next(csv.DictReader(f))
    assert row["overall_urgency"] == "ROUTINE"


@pytest.mark.parametrize("value", ["True", "true", "1", "yes"])
def test_main_batch_true_is_critical(value, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with open("inputs.csv", "w", newline="", encoding="utf-8") as f:
        f.write("task_id,target_identifier,primary_metric,secondary_metric,is_critical_flag\n")
        f.write("T1,SAMPLE-1,1,1," + value + "\n")
    assert main_cli(["batch", "-i", "inputs.csv", "-o", "outputs.csv"]) == 0
    with open("outputs.csv", encoding="utf-8") as f:
        assert next(csv.DictReader(f))["overall_urgency"] == "CRITICAL_STAT_PANIC"


def test_main_batch_missing_required_columns(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "inputs.csv").write_text("task_id,primary_metric\nT1,1\n")
    with pytest.raises(ValueError, match="Missing required"):
        main_cli(["batch", "-i", "inputs.csv", "-o", "outputs.csv"])


def test_main_batch_rejects_unknown_boolean(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "inputs.csv").write_text(
        "task_id,target_identifier,primary_metric,is_critical_flag\nT1,SAMPLE-1,1,maybe\n"
    )
    with pytest.raises(ValueError, match="Invalid CSV boolean"):
        main_cli(["batch", "-i", "inputs.csv", "-o", "outputs.csv"])


def test_frontier_false_not_critical(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "inputs.csv").write_text(
        "task_id,target_identifier,primary_metric,secondary_metric,is_critical_flag\n"
        "T1,SAMPLE-1,1,1,False\n"
    )
    assert frontier_cli(["batch", "-i", "inputs.csv", "-o", "outputs.csv"]) == 0
    with open("outputs.csv", encoding="utf-8") as f:
        assert next(csv.DictReader(f))["overall_status"] == "NOMINAL_OPTIMAL"


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), float("-inf")])
def test_reject_non_finite_metrics(invalid):
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="T1", target_identifier="SAMPLE-1", primary_metric=invalid)


def test_api_exposes_ui_and_rejects_phi(monkeypatch):
    from fastapi.testclient import TestClient
    client = TestClient(app)
    assert client.get("/").status_code == 200
    assert client.get("/app.js").status_code == 200
    assert client.get("/health").status_code == 200
    response = client.post("/api/audit", json={
        "task_id": "MRN-12345678", "target_identifier": "SAMPLE-1",
        "primary_metric": 1, "secondary_metric": 1
    })
    assert response.status_code == 422
    assert "12345678" not in response.text


def test_api_logs_require_token(monkeypatch):
    from fastapi.testclient import TestClient
    client = TestClient(app)
    monkeypatch.delenv("AUDIT_LOGS_TOKEN", raising=False)
    assert client.get("/api/audit/logs").status_code == 503
    monkeypatch.setenv("AUDIT_LOGS_TOKEN", "test-token")
    assert client.get("/api/audit/logs").status_code == 403
    assert client.get("/api/audit/logs", headers={"x-audit-token": "bad"}).status_code == 403
    assert client.get("/api/audit/logs", headers={"x-audit-token": "test-token"}).status_code == 200
