"""Context Signals Model according to Section 6 of IT Navigator Build Spec."""
from typing import List, Optional
from pydantic import BaseModel, Field


class UserContext(BaseModel):
    id: str = Field(default="u00000", description="Unique user identifier")
    name: Optional[str] = Field(default="Employee", description="User full name")
    department: str = Field(default="General", description="Department name")
    role: str = Field(default="Employee", description="User business role")
    location: Optional[str] = Field(default=None, description="Office location or remote region")
    manager_id: Optional[str] = Field(default=None, description="Manager ID for approval routing")


class IssueContext(BaseModel):
    raw_text: str = Field(..., description="Original problem statement from the employee")
    detected_intent: str = Field(default="general_inquiry", description="Extracted intent code")
    affected_service: Optional[str] = Field(default=None, description="Affected application or system")
    stated_urgency: str = Field(default="medium", description="User stated urgency: low, medium, high, critical")
    time_sensitivity_minutes: Optional[int] = Field(default=None, description="Reported deadline in minutes")
    prior_resolve_attempted: bool = Field(default=False, description="Whether a self-service fix was already attempted and failed")


class ServiceContext(BaseModel):
    business_criticality: str = Field(default="Tier 3", description="Criticality tier: Tier 1, Tier 2, Tier 3")
    current_health_status: str = Field(default="healthy", description="Status: healthy, degraded, down")
    known_open_incidents: int = Field(default=0, description="Active open incident count in ITSM")
    similar_reports_last_hour: int = Field(default=0, description="Cluster of similar reports last 60 minutes")


class PolicyContext(BaseModel):
    user_access_level: str = Field(default="standard", description="standard, elevated, privileged, admin")
    existing_entitlements: List[str] = Field(default_factory=list, description="List of currently assigned entitlements")
    requires_privileged_flag: bool = Field(default=False, description="Flag indicating if the action requires privileged access")


class SecuritySignal(BaseModel):
    flag: bool = Field(default=False, description="True if security risk or incident detected")
    confidence: float = Field(default=0.0, description="Confidence score between 0.0 and 1.0")
    category: Optional[str] = Field(default=None, description="Security category: data_leak, unauthorized_access, account_takeover, phishing, etc.")


class SituationContext(BaseModel):
    user: UserContext = Field(default_factory=UserContext)
    issue: IssueContext
    service_context: ServiceContext = Field(default_factory=ServiceContext)
    policy_context: PolicyContext = Field(default_factory=PolicyContext)
    security_signal: SecuritySignal = Field(default_factory=SecuritySignal)
    kb_match_confidence: float = Field(default=0.0, description="Confidence of candidate KB article (0.0 to 1.0)")
    kb_match_is_safe: bool = Field(default=False, description="True if KB candidate fix is classified safe")
    kb_match_article_id: Optional[str] = Field(default=None, description="Candidate KB article ID")
