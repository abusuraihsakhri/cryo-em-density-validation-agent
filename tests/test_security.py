"""
Security-focused test suite for cryo-em-density-validation-agent.
Tests HMAC integrity, path traversal protection, and PHI guard enforcement.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from agents.base import PHIGuard, AuditLogger, AuditTrail, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from cli import main


class TestHMACIntegrity:
    """Test HMAC-SHA256 audit trail integrity verification."""

    def test_audit_trail_signature_verification(self):
        """Verify that HMAC signatures are correctly validated."""
        trail = AuditTrail(secret_key="test-key-for-verification")
        trail.log("test_actor", "tier1", "TEST_EVENT", {"data": "value1"})
        trail.log("test_actor", "tier1", "TEST_EVENT", {"data": "value2"})
        assert trail.verify_integrity() is True

    def test_audit_trail_tamper_detection(self):
        """Verify that tampering with audit entries is detected."""
        trail = AuditTrail(secret_key="test-key-for-tamper")
        trail.log("test_actor", "tier1", "TEST_EVENT", {"data": "original"})
        # Tamper with the payload hash
        trail.logs[0]["payload_hash"] = "tampered_hash_value"
        assert trail.verify_integrity() is False

    def test_audit_trail_chain_verification(self):
        """Verify that chain linkage is validated."""
        trail = AuditTrail(secret_key="test-key-for-chain")
        trail.log("actor1", "tier1", "EVENT1", {"k": "v1"})
        trail.log("actor2", "tier1", "EVENT2", {"k": "v2"})
        trail.log("actor3", "tier1", "EVENT3", {"k": "v3"})
        assert trail.verify_integrity() is True
        assert len(trail.get_trail()) == 3

    def test_audit_trail_empty(self):
        """Empty audit trail should pass verification."""
        trail = AuditTrail(secret_key="test-key-empty")
        assert trail.verify_integrity() is True

    def test_audit_trail_prev_hash_tamper(self):
        """Tampering with prev_hash should be detected."""
        trail = AuditTrail(secret_key="test-key-prevhash")
        trail.log("actor1", "tier1", "EVENT1", {"k": "v1"})
        trail.log("actor2", "tier1", "EVENT2", {"k": "v2"})
        # Break the chain
        trail.logs[1]["prev_hash"] = "broken_chain_hash"
        assert trail.verify_integrity() is False


class TestPHIGuard:
    """Test PHI outbound guard enforcement."""

    def test_mrn_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient MRN-12345678")

    def test_ssn_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("SSN: 123-45-6789")

    def test_phone_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Call patient at (555) 123-4567")

    def test_email_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Email patient at john@example.com")

    def test_dob_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("DOB: 01/15/1985")

    def test_patient_name_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient Name: John Smith")

    def test_redact_phi(self):
        result = PHIGuard.redact_phi("Patient MRN-12345678 and SSN 123-45-6789")
        assert "MRN" not in result
        assert "123-45-6789" not in result
        assert "[REDACTED_IDENTIFIER]" in result

    def test_clean_text_passes(self):
        PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")
        PHIGuard.assert_no_phi("Task TASK-2026-001 processed successfully")

    def test_supervisor_blocks_phi_task_id(self):
        supervisor = SystemSupervisor(model_provider="mock")
        payload = SystemTaskPayload(
            task_id="TASK-MRN-12345678",
            target_identifier="KEY-01",
            primary_metric=10.0,
        )
        with pytest.raises(SecurityException):
            supervisor.process_task(payload)


class TestPathTraversalProtection:
    """Test path traversal protection in batch CLI."""

    def test_batch_safe_path(self, tmp_path):
        """Test that batch processing works with safe paths within working directory."""
        # Create temp files inside the working directory so they pass path traversal check
        input_file = Path("test_input_tmp.csv")
        output_file = Path("test_output_tmp.csv")
        try:
            input_file.write_text("task_id,target_identifier,primary_metric,secondary_metric\nT1,KEY-01,10.0,5.0\n")
            main(["batch", "-i", str(input_file), "-o", str(output_file)])
            assert output_file.exists()
            # Verify output content
            content = output_file.read_text()
            assert "overall_urgency" in content
        finally:
            if input_file.exists():
                input_file.unlink()
            if output_file.exists():
                output_file.unlink()

    def test_path_traversal_blocked(self):
        """Test that path traversal attempts are blocked."""
        with pytest.raises(ValueError, match="Path traversal detected"):
            main(["batch", "-i", "../../../etc/passwd", "-o", "results.csv"])

    def test_path_traversal_output_blocked(self):
        """Test that output path traversal attempts are blocked."""
        with pytest.raises(ValueError, match="Path traversal detected"):
            main(["batch", "-i", "sample.csv", "-o", "../../tmp/evil.csv"])


class TestAuditLogger:
    """Test the global AuditLogger interface."""

    def test_global_audit_log(self):
        entry = AuditLogger.log("test", "tier", "TEST", {"key": "value"})
        assert "audit_id" in entry
        assert "current_hash" in entry
        assert entry["actor"] == "test"

    def test_global_audit_verify(self):
        AuditLogger.log("test", "tier", "TEST", {"key": "value"})
        assert AuditLogger.verify_integrity() is True
