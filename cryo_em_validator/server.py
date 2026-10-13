"""
FastAPI REST API Server for CryoEM-Validator: Fourier Shell Correlation (FSC) & Local Resolution Agent.
"""
from typing import Dict, Any
from .models import FrontierPayload
from .agents import CryoEMValidatorCoordinator

coordinator = CryoEMValidatorCoordinator()


def create_app():
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel, Field
        from agents.base import SecurityException

        app = FastAPI(
            title="Cryo-EM Illustrative Metadata Screening (Legacy API)",
            description="Screens scalar metadata against illustrative thresholds. Does not calculate FSC, map-to-model correlation, or atomic clashes.",
            version="2.0.0-FRONTIER",
        )

        class TaskRequest(BaseModel):
            task_id: str = "TASK-2026-001"
            target_identifier: str = "TARGET-BIO-KEY"
            primary_metric: float = Field(default=28.5, allow_inf_nan=False)
            secondary_metric: float = Field(default=14.2, allow_inf_nan=False)
            status_descriptor: str = "DISCORDANT_ANOMALY"
            is_critical_flag: bool = True
            attributes: Dict[str, Any] = Field(default_factory=dict)

        class ChatRequest(BaseModel):
            query: str

        @app.get("/health")
        def health():
            return {"status": "HEALTHY", "system": "cryo-em-density-validation-agent", "domain": "Biomedical Scientific Discovery & Multi-Omics", "version": "2.0.0-FRONTIER"}

        @app.post("/api/audit")
        def api_audit(req: TaskRequest):
            payload = FrontierPayload(
                task_id=req.task_id,
                target_identifier=req.target_identifier,
                primary_metric=req.primary_metric,
                secondary_metric=req.secondary_metric,
                status_descriptor=req.status_descriptor,
                is_critical_flag=req.is_critical_flag,
                attributes=req.attributes,
            )
            try:
                return coordinator.process(payload)
            except SecurityException:
                raise HTTPException(status_code=422, detail="Potential sensitive identifier in request") from None

        @app.post("/api/chat")
        def api_chat(req: ChatRequest):
            try:
                return {"response": coordinator.query_supervisory_chat(req.query)}
            except SecurityException:
                raise HTTPException(status_code=422, detail="Potential sensitive identifier in request") from None

        return app
    except ImportError:
        return None
