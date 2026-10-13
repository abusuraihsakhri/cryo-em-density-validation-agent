"""Regression coverage for audit record isolation, CSV round trips and safe defaults."""

import csv

import pytest
from fastapi.testclient import TestClient

from agents.api import app
from agents.base import AuditTrail
from cli import main as main_cli
from cryo_em_validator.cli import main as legacy_cli
from simulator import run_simulation


@pytest.mark.parametrize(
    ("cli", "result_columns"),
    [
        (main_cli, ("overall_urgency", "integrity_status", "total_alerts", "audit_hash")),
        (legacy_cli, ("overall_status", "total_alerts", "critical_count", "consensus_summary")),
    ],
)
def test_batch_output_can_be_reprocessed_without_duplicate_headers(
    cli, result_columns, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "input.csv").write_text(
        "task_id,target_identifier,primary_metric,secondary_metric,status_descriptor\n"
        "T1,SAMPLE-1,1,1,NOMINAL\n",
        encoding="utf-8",
    )
    assert cli(["batch", "-i", "input.csv", "-o", "first.csv"]) == 0
    assert cli(["batch", "-i", "first.csv", "-o", "second.csv"]) == 0

    with open("second.csv", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames is not None
        assert len(reader.fieldnames) == len(set(reader.fieldnames))
        for name in result_columns:
            assert reader.fieldnames.count(name) == 1
        rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["total_alerts"] == "0"


def test_audit_trail_public_results_are_defensive_copies():
    trail = AuditTrail(secret_key="testing-only")
    returned_entry = trail.log("tester", "tier", "TEST", {"status": "nominal"})
    returned_entry["current_hash"] = "modified"
    retrieved = trail.get_trail()
    retrieved[0]["payload_hash"] = "modified"
    retrieved.clear()

    assert len(trail.get_trail()) == 1
    assert trail.verify_integrity() is True


@pytest.mark.parametrize("iterations", [0, -1])
def test_simulation_rejects_non_positive_task_count(iterations):
    with pytest.raises(ValueError, match="positive integer"):
        run_simulation(iterations)


def test_health_does_not_claim_external_standard_conformance():
    health = TestClient(app).get("/health")
    assert health.status_code == 200
    assert "no external standard conformance" in health.json()["standard"]


def test_legacy_api_rejects_non_finite_metrics_and_sensitive_identifiers():
    from cryo_em_validator.server import create_app

    legacy = TestClient(create_app())
    base = {
        "task_id": "T1", "target_identifier": "SAMPLE-1",
        "primary_metric": 1, "secondary_metric": 1,
        "status_descriptor": "NOMINAL",
    }
    assert legacy.post("/api/audit", json=base).status_code == 200
    for field in ("primary_metric", "secondary_metric"):
        assert legacy.post(
            "/api/audit", json={**base, field: "NaN"}
        ).status_code == 422
    response = legacy.post(
        "/api/audit", json={**base, "task_id": "MRN-12345678"}
    )
    assert response.status_code == 422
    assert "12345678" not in response.text

    response = legacy.post("/api/chat", json={"query": "MRN-12345678"})
    assert response.status_code == 422
