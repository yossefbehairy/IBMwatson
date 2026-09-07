"""Major Incident Engine module (Section 7.3 of Build Spec).
Evaluates deterministic Major Incident candidacy.
Note: A major_incident_candidate NEVER auto-declares; it always flags for human (MIM) sign-off.
"""
from src.models.context import SituationContext
from src.models.decisions import MajorIncidentDecision

DEFAULT_AFFECTED_USERS_THRESHOLD = 3


def evaluate_major_incident(
    context: SituationContext,
    affected_users_threshold: int = DEFAULT_AFFECTED_USERS_THRESHOLD,
) -> MajorIncidentDecision:
    """Evaluates whether the situation meets Major Incident criteria:
    1. Criticality = Tier 1 and affected users >= threshold (or degraded with cluster).
    2. security_signal.flag = true.
    3. Complete outage (health_status = 'down') on Tier 1 or Tier 2.
    4. Executive or media visibility flag.
    """
    svc = context.service_context
    sec = context.security_signal
    crit = (svc.business_criticality or "Tier 3").strip()
    status = (svc.current_health_status or "healthy").strip().lower()
    reports = svc.similar_reports_last_hour

    # Criterion 1: Active Security Signal
    if sec.flag:
        return MajorIncidentDecision(
            major_incident_candidate=True,
            reasoning_code="SECURITY_INCIDENT_ESCALATION",
            requires_human_signoff=True,
        )

    # Criterion 2: Complete Outage on Tier 1 or Tier 2 Service
    if status == "down" and crit in ["Tier 1", "Tier 2"]:
        return MajorIncidentDecision(
            major_incident_candidate=True,
            reasoning_code="CRITICAL_SERVICE_COMPLETE_OUTAGE",
            requires_human_signoff=True,
        )

    # Criterion 3: Tier 1 Service with Affected Users >= Threshold or Degraded Cluster
    if crit == "Tier 1" and (reports >= affected_users_threshold or (status == "degraded" and reports >= 2)):
        return MajorIncidentDecision(
            major_incident_candidate=True,
            reasoning_code="TIER1_HIGH_IMPACT_CLUSTER",
            requires_human_signoff=True,
        )

    # Criterion 4: Executive / Media Visibility
    raw_lower = context.issue.raw_text.lower()
    if any(k in raw_lower for k in ["executive", "ceo", "board meeting", "press", "media", "c-suite"]):
        return MajorIncidentDecision(
            major_incident_candidate=True,
            reasoning_code="EXECUTIVE_VISIBILITY_IMPACT",
            requires_human_signoff=True,
        )

    return MajorIncidentDecision(
        major_incident_candidate=False,
        reasoning_code="CRITERIA_NOT_MET",
        requires_human_signoff=True,
    )
