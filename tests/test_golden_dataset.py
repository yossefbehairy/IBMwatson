"""Golden Test Dataset (Section 12 of Build Spec).
Release Gate: All 9 categories must pass before go-live.
Enforces ZERO TOLERANCE on the Security — Implicit category.
"""
import sys
import os
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.orchestrator.runner import execute_pipeline


# ==================== 1. Clear Resolve ====================


def test_category_1_clear_resolve():
    """Known, safe fix exists in KB and is offered directly to employee."""
    query = "My VPN keeps disconnecting whenever I join a video call"
    res = execute_pipeline(query)

    assert res["pathway_decision"]["recommended_pathway"] == "resolve"
    assert res["collaborator"] == "it_knowledge_agent"
    assert "article_id" in res["action_taken"]
    assert "AnyConnect" in res["response"]


# ==================== 2. Clear Request ====================


def test_category_2_clear_request():
    """Provisioning need correctly identified as Request, no false Escalate."""
    query = "I need access to the design system Figma file for my new marketing project"
    res = execute_pipeline(query)

    assert res["pathway_decision"]["recommended_pathway"] == "request"
    assert res["collaborator"] == "service_request_agent"
    assert "request_id" in res["action_taken"]


# ==================== 3. Clear Escalate ====================


def test_category_3_clear_escalate():
    """Break/fix with no safe KB solution routes to Escalate."""
    query = "The expense app has been throwing a 500 error all morning and won't load"
    res = execute_pipeline(query)

    assert res["pathway_decision"]["recommended_pathway"] == "escalate"
    assert res["collaborator"] == "incident_management_agent"
    assert "incident_id" in res["action_taken"]


# ==================== 4. Ambiguous / Borderline (Clarify) ====================


def test_category_4_ambiguous_borderline():
    """Vague query without service or error details routes to Clarify, not guessing."""
    query = "it's being weird"
    res = execute_pipeline(query)

    assert res["pathway_decision"]["recommended_pathway"] == "clarify"
    assert "specify which application" in res["response"]


# ==================== 5. Security — Explicit Wording ====================


def test_category_5_security_explicit():
    """Explicit security wording triggers fast-path Escalate with security flag."""
    query = "I think my account got hacked, there are suspicious logins"
    res = execute_pipeline(query)

    assert res["context"]["security_signal"]["flag"] is True
    assert res["pathway_decision"]["recommended_pathway"] == "escalate"
    assert res["action_taken"]["major_incident_candidate"] is True


# ==================== 6. Security — Implicit / No Keywords (ZERO TOLERANCE) ====================


def test_category_6_security_implicit():
    """ZERO TOLERANCE RELEASE GATE: Implicit data leakage without security words MUST Escalate."""
    query = "I can see a colleague's client records that I shouldn't have access to"
    res = execute_pipeline(query)

    assert res["context"]["security_signal"]["flag"] is True, "CRITICAL: Failed to detect implicit security risk!"
    assert res["pathway_decision"]["recommended_pathway"] == "escalate"
    assert res["action_taken"]["major_incident_candidate"] is True


# ==================== 7. Conflicting Context ====================


def test_category_7_conflicting_context_urgency_inflation():
    """User screams URGENT on a Tier 3 internal tool; Policy Engine holds priority to P4."""
    query = "URGENT EMERGENCY!! The second floor printer is out of paper immediately!!"
    res = execute_pipeline(query)

    # Stated urgency was high, but criticality is Tier 3 and single device -> must be P4!
    assert res["action_taken"]["priority"] == "P4"
    assert res["action_taken"]["sla_hours"] == 24.0


# ==================== 8. Gaming Attempts ====================


def test_category_8_gaming_attempts():
    """Urgency language inflation cannot artificially escalate access requests or priority."""
    query = "I need a secondary monitor ASAP within 5 minutes or everything crashes!"
    res = execute_pipeline(query)

    # It is a hardware request -> routes to Request, requires line manager approval
    assert res["pathway_decision"]["recommended_pathway"] == "request"
    assert res["collaborator"] == "service_request_agent"
    assert res["action_taken"]["status"] == "Pending Approval"
    assert res["action_taken"]["approver"] == "Line manager"


# ==================== 9. Duplicate Incident Merge ====================


def test_category_9_duplicate_incident_merge():
    """Section 10 Scenario: Multiple employees reporting degraded Tier 1 service merge to existing ticket."""
    query = "I can't access Salesforce and I have a client meeting in 20 minutes."
    res = execute_pipeline(query)

    assert res["pathway_decision"]["recommended_pathway"] == "escalate"
    assert res["collaborator"] == "incident_management_agent"
    # Merged into open INC0004521
    assert res["action_taken"]["incident_id"] == "INC0004521"
    assert res["action_taken"]["is_duplicate_merged"] is True
    assert res["action_taken"]["major_incident_candidate"] is True
    assert "INC0004521" in res["response"]
