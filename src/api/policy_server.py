"""FastAPI implementation of IT Navigator Policy Engine (Appendix A).
Exposes independent OpenAPI operations for Watson Orchestrate tools.
"""
import sys
import os
from typing import Optional
from fastapi import FastAPI, Body
from pydantic import BaseModel, Field

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.models.context import SituationContext, SecuritySignal
from src.models.decisions import (
    PathwayDecision,
    PriorityDecision,
    MajorIncidentDecision,
    EligibilityDecision,
)
from src.policy_engine.pathway_resolver import resolve_pathway as core_resolve_pathway
from src.policy_engine.priority_engine import evaluate_priority as core_evaluate_priority
from src.policy_engine.major_incident_engine import evaluate_major_incident as core_evaluate_major_incident
from src.policy_engine.eligibility_engine import evaluate_eligibility_and_approval as core_evaluate_eligibility
from src.security.security_classifier import classify_security_risk as core_classify_security
from src.connectors.context_provider import get_context_provider

app = FastAPI(
    title="IT Navigator Policy Engine",
    description="Deterministic policy engine and context services for IBM watsonx Orchestrate",
    version="1.0.0",
)


class ContextRequest(BaseModel):
    context: SituationContext


class RawTextRequest(BaseModel):
    raw_text: str = Field(..., description="Problem description or employee message")
    user_id: str = Field(default="u12345", description="Employee user ID")
    override_service: Optional[str] = None
    override_urgency: Optional[str] = None
    prior_resolve_attempted: bool = False


class EligibilityRequest(BaseModel):
    context: SituationContext
    requested_item: str = Field(default="", description="Specific catalog item name")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "IT Navigator Policy Engine", "version": "1.0.0"}


@app.post(
    "/resolve-pathway",
    response_model=PathwayDecision,
    operation_id="resolve_pathway",
    summary="Deterministic pathway selection (Resolve / Request / Escalate / Clarify) — Section 7.1",
    tags=["Policy Engine"],
)
def resolve_pathway_endpoint(payload: ContextRequest):
    return core_resolve_pathway(payload.context)


@app.post(
    "/evaluate-priority",
    response_model=PriorityDecision,
    operation_id="evaluate_priority",
    summary="Deterministic priority + SLA from business criticality, users affected, urgency — Section 7.2",
    tags=["Policy Engine"],
)
def evaluate_priority_endpoint(payload: ContextRequest):
    return core_evaluate_priority(payload.context)


@app.post(
    "/evaluate-major-incident",
    response_model=MajorIncidentDecision,
    operation_id="evaluate_major_incident",
    summary="Deterministic major-incident candidacy flag — Section 7.3",
    tags=["Policy Engine"],
)
def evaluate_major_incident_endpoint(payload: ContextRequest):
    return core_evaluate_major_incident(payload.context)


@app.post(
    "/evaluate-eligibility-approval",
    response_model=EligibilityDecision,
    operation_id="evaluate_eligibility_and_approval",
    summary="Deterministic access eligibility and approval routing — Section 7.4",
    tags=["Policy Engine"],
)
def evaluate_eligibility_endpoint(payload: EligibilityRequest):
    return core_evaluate_eligibility(payload.context, payload.requested_item)


@app.post(
    "/classify-security",
    response_model=SecuritySignal,
    operation_id="classify_security_risk",
    summary="Semantic and pattern security risk detector — Section 5.4",
    tags=["Security Classifier"],
)
def classify_security_endpoint(payload: RawTextRequest):
    return core_classify_security(payload.raw_text)


@app.post(
    "/get-context",
    response_model=SituationContext,
    operation_id="get_context",
    summary="Unified Situation Object assembler — Section 6",
    tags=["Context Layer"],
)
def get_context_endpoint(payload: RawTextRequest):
    provider = get_context_provider()
    return provider.assemble_context(
        raw_text=payload.raw_text,
        user_id=payload.user_id,
        override_service=payload.override_service,
        override_urgency=payload.override_urgency,
        prior_resolve_attempted=payload.prior_resolve_attempted,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
