"""
FastAPI REST API Server for Cryo Em Density Validation Agent.
"""
import os
import hmac
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from .base import AuditLogger, PHIGuard, SecurityException
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Cryo Em Density Validation Agent API",
    description="Illustrative scalar metadata screening. Does not calculate FSC or validate cryo-EM maps.",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "cryo-em-density-validation-agent", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "RUNNING"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
    except SecurityException:
        raise HTTPException(status_code=422, detail='Potential sensitive identifier in request') from None
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except SecurityException:
        raise HTTPException(status_code=422, detail='Potential sensitive identifier in request') from None


@app.get("/api/audit/logs")
def api_audit_logs(x_audit_token: Optional[str] = Header(default=None)):
    """Protect ledger metadata: do not expose it anonymously."""
    required = os.environ.get("AUDIT_LOGS_TOKEN", "")
    if not required:
        raise HTTPException(status_code=503, detail="Audit log access not configured")
    if not x_audit_token or not hmac.compare_digest(x_audit_token, required):
        raise HTTPException(status_code=403, detail="Audit token required")
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


# Register static UI last so explicit API endpoints remain reachable.
app.mount("/", StaticFiles(directory=str(Path(__file__).resolve().parent.parent / "web"), html=True), name="web")
