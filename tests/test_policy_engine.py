"""Unit tests for the 4 Deterministic Policy Engine modules.
Verifies exhaustive branch coverage across Priority, SLA, Major Incident, Eligibility, and Pathway rules.
"""
import sys
import os
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.models.context import (
    UserContext,
    IssueContext,
    ServiceContext,
    PolicyContext,
    SecuritySignal,
    SituationContext,
)
from src.policy_engine.pathway_resolver import resolve_pathway
from src.policy_engine.priority_engine import evaluate_priority
from src.policy_engine.major_incident_engine import evaluate_major_incident
from src.policy_engine.eligibility_engine import evaluate_eligibility_and_approval


def make_context(
    raw_text: str = "Test issue",
    service: str = "Salesforce",
    criticality: str = "Tier 1",
    health: str = "healthy",
    similar_reports: int = 0,
    urgency: str = "medium",
    sec_flag: bool = False,
    kb_safe: bool = False,
    kb_conf: float = 0.0,
    prior_failed: bool = False,
    role: str = "Account Executive",
    privileged: bool = False,
) -> SituationContext:
    return SituationContext(
        user=UserContext(id="u101", name="Test User", role=role, department="Sales"),
        issue=IssueContext(
            raw_text=raw_text,
            detected_intent="break_fix",
            affected_service=service,
            stated_urgency=urgency,
            prior_resolve_attempted=prior_failed,
        ),
        service_context=ServiceContext(
            business_criticality=criticality,
            current_health_status=health,
            similar_reports_last_hour=similar_reports,
        ),
        policy_context=PolicyContext(
            user_access_level="standard",
            existing_entitlements=["Salesforce - Standard User"],
            requires_privileged_flag=privileged,
        ),
        security_signal=SecuritySignal(
            flag=sec_flag,
            confidence=1.0 if sec_flag else 0.05,
            category="test_sec" if sec_flag else None,
        ),
        kb_match_is_safe=kb_safe,
        kb_match_confidence=kb_conf,
    )


# ==================== 1. Pathway Resolver Tests ====================


def test_pathway_security_override():
    """Security flag must unconditionally route to Escalate, ignoring KB matches."""
    ctx = make_context(sec_flag=True, kb_safe=True, kb_conf=0.99)
    res = resolve_pathway(ctx)
    assert res.recommended_pathway == "escalate"
    assert res.reasoning_code == "SECURITY_SIGNAL_ACTIVE"


def test_pathway_prior_resolve_failed():
    """Failed resolve must fall through to Escalate."""
    ctx = make_context(prior_failed=True, kb_safe=True, kb_conf=0.90)
    res = resolve_pathway(ctx)
    assert res.recommended_pathway == "escalate"
    assert res.reasoning_code == "PRIOR_RESOLVE_FAILED"


def test_pathway_safe_kb_match():
    """Safe high-confidence KB match routes to Resolve."""
    ctx = make_context(raw_text="VPN keeps disconnecting", kb_safe=True, kb_conf=0.85)
    res = resolve_pathway(ctx)
    assert res.recommended_pathway == "resolve"
    assert res.reasoning_code == "SAFE_KB_MATCH_AVAILABLE"


def test_pathway_service_outage_degraded():
    """Service degradation with cluster reports routes to Escalate."""
    ctx = make_context(health="degraded", similar_reports=3)
    res = resolve_pathway(ctx)
    assert res.recommended_pathway == "escalate"
    assert res.reasoning_code == "SERVICE_OUTAGE_OR_CLUSTER"


def test_pathway_provisioning_request():
    """Catalog requests route to Request pathway."""
    ctx = make_context(raw_text="I need access to Salesforce - Standard User for my role")
    ctx.issue.detected_intent = "software_request"
    res = resolve_pathway(ctx)
    assert res.recommended_pathway == "request"
    assert res.reasoning_code == "PROVISIONING_REQUEST_DETECTED"


def test_pathway_ambiguous_clarify():
    """Ambiguous query without service or details routes to Clarify."""
    ctx = make_context(raw_text="it's not working", service="")
    ctx.issue.affected_service = None
    ctx.issue.detected_intent = "clarify"
    res = resolve_pathway(ctx)
    assert res.recommended_pathway == "clarify"
    assert res.reasoning_code == "AMBIGUOUS_SIGNAL_NEEDS_CLARIFICATION"
    assert res.missing_signal is not None


# ==================== 2. Priority Engine Tests ====================


def test_priority_matrix_tier1_multiple_high():
    ctx = make_context(criticality="Tier 1", similar_reports=4, urgency="high")
    res = evaluate_priority(ctx)
    assert res.priority == "P1"
    assert res.response_sla_hours == 0.25
    assert res.resolution_sla_hours == 4.0


def test_priority_matrix_tier1_single_high():
    ctx = make_context(criticality="Tier 1", similar_reports=0, urgency="high")
    res = evaluate_priority(ctx)
    assert res.priority == "P2"
    assert res.response_sla_hours == 1.0


def test_priority_matrix_tier1_low():
    ctx = make_context(criticality="Tier 1", similar_reports=0, urgency="low")
    res = evaluate_priority(ctx)
    assert res.priority == "P3"
    assert res.response_sla_hours == 4.0


def test_priority_matrix_tier2_multiple_high():
    ctx = make_context(criticality="Tier 2", similar_reports=2, urgency="high")
    res = evaluate_priority(ctx)
    assert res.priority == "P2"


def test_priority_matrix_tier2_single_any():
    ctx = make_context(criticality="Tier 2", similar_reports=0, urgency="high")
    res = evaluate_priority(ctx)
    assert res.priority == "P3"


def test_priority_matrix_tier3():
    ctx = make_context(criticality="Tier 3", similar_reports=10, urgency="critical")
    res = evaluate_priority(ctx)
    assert res.priority == "P4"
    assert res.response_sla_hours == 24.0


# ==================== 3. Major Incident Engine Tests ====================


def test_major_incident_security_signal():
    ctx = make_context(sec_flag=True)
    res = evaluate_major_incident(ctx)
    assert res.major_incident_candidate is True
    assert res.reasoning_code == "SECURITY_INCIDENT_ESCALATION"
    assert res.requires_human_signoff is True


def test_major_incident_tier1_cluster():
    ctx = make_context(criticality="Tier 1", similar_reports=5)
    res = evaluate_major_incident(ctx)
    assert res.major_incident_candidate is True
    assert res.reasoning_code == "TIER1_HIGH_IMPACT_CLUSTER"


def test_major_incident_service_down():
    ctx = make_context(criticality="Tier 1", health="down")
    res = evaluate_major_incident(ctx)
    assert res.major_incident_candidate is True
    assert res.reasoning_code == "CRITICAL_SERVICE_COMPLETE_OUTAGE"


def test_major_incident_negative():
    ctx = make_context(criticality="Tier 2", health="healthy", similar_reports=0)
    res = evaluate_major_incident(ctx)
    assert res.major_incident_candidate is False


# ==================== 4. Eligibility & Approval Tests ====================


def test_eligibility_standard_auto_approved():
    ctx = make_context(role="Account Executive")
    res = evaluate_eligibility_and_approval(ctx, requested_item="Salesforce - Standard User")
    assert res.is_eligible is True
    assert res.approval_required is False
    assert res.is_privileged is False


def test_eligibility_non_standard_manager_approval():
    ctx = make_context(role="Account Executive")
    res = evaluate_eligibility_and_approval(ctx, requested_item="Figma Professional License")
    assert res.is_eligible is True
    assert res.approval_required is True
    assert res.approver_role == "Line manager"
    assert res.is_privileged is False


def test_eligibility_hardware_approval():
    ctx = make_context(raw_text="I need a new secondary monitor for my home desk")
    res = evaluate_eligibility_and_approval(ctx, requested_item="Secondary Monitor")
    assert res.is_eligible is True
    assert res.approval_required is True
    assert res.approver_role == "Line manager"


def test_eligibility_privileged_security_approval():
    ctx = make_context(raw_text="I need AWS Production Admin root access for database maintenance", privileged=True)
    res = evaluate_eligibility_and_approval(ctx, requested_item="AWS Production Admin")
    assert res.is_eligible is True
    assert res.approval_required is True
    assert res.approver_role == "IT Security"
    assert res.is_privileged is True
