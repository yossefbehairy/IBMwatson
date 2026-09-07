"""Decision models produced by the Deterministic Policy Engine."""
from typing import Optional, Literal
from pydantic import BaseModel, Field


class PathwayDecision(BaseModel):
    recommended_pathway: Literal["resolve", "request", "escalate", "clarify"] = Field(
        ..., description="Deterministic pathway recommendation"
    )
    reasoning_code: str = Field(..., description="Deterministic rule audit code")
    missing_signal: Optional[str] = Field(
        default=None, description="Populated only when recommended_pathway=clarify"
    )


class PriorityDecision(BaseModel):
    priority: Literal["P1", "P2", "P3", "P4"] = Field(
        ..., description="Computed incident priority"
    )
    response_sla_hours: float = Field(..., description="Target response SLA in hours")
    resolution_sla_hours: float = Field(..., description="Target resolution SLA in hours")
    reasoning_code: str = Field(..., description="Deterministic matrix lookup code")


class MajorIncidentDecision(BaseModel):
    major_incident_candidate: bool = Field(
        ..., description="Whether this situation qualifies as a candidate for Major Incident declaration"
    )
    reasoning_code: str = Field(..., description="Rule code triggering major incident candidacy")
    requires_human_signoff: bool = Field(
        default=True, description="Always True; major incidents never auto-declare"
    )


class EligibilityDecision(BaseModel):
    is_eligible: bool = Field(..., description="Whether user role qualifies for requested item")
    approval_required: bool = Field(..., description="Whether approval is required before provisioning")
    approver_role: Optional[str] = Field(
        default=None, description="Role of the required approver (e.g. Line manager, IT Security)"
    )
    is_privileged: bool = Field(
        default=False, description="Whether the entitlement confers elevated or privileged access"
    )
    reasoning_code: str = Field(..., description="Eligibility and approval rule code")
