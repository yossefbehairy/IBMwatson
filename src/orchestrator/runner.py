"""Interactive Simulator and Conversation Runner for IT Navigator.
Demonstrates the full three-layer decision pipeline:
1. AI Reasoning & Signal Extraction
2. Deterministic Policy Engine (Pathway / Priority / Eligibility / Major Incident)
3. Specialized Collaborator Execution & HITL Gates
"""
import sys
import os
import argparse
import json
from typing import Dict, Any, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.connectors.context_provider import get_context_provider
from src.security.security_classifier import classify_security_risk
from src.policy_engine.pathway_resolver import resolve_pathway
from src.policy_engine.priority_engine import evaluate_priority
from src.policy_engine.major_incident_engine import evaluate_major_incident
from src.policy_engine.eligibility_engine import evaluate_eligibility_and_approval
from src.connectors.mock_itsm import get_itsm_client
from src.connectors.mock_iam import get_iam_client
from src.connectors.mock_kb import get_kb_client
from watson_orchestrate_client import WatsonOrchestrateClient


def execute_pipeline(
    raw_query: str,
    user_id: str = "u12345",
    prior_resolve_attempted: bool = False,
) -> Dict[str, Any]:
    """Runs the deterministic orchestration pipeline for an employee query."""
    provider = get_context_provider()
    itsm = get_itsm_client()
    iam = get_iam_client()
    kb = get_kb_client()

    # Step 1: Context Assembly & Signal Extraction
    context = provider.assemble_context(
        raw_text=raw_query,
        user_id=user_id,
        prior_resolve_attempted=prior_resolve_attempted,
    )

    # Step 2: Deterministic Pathway Resolution (Section 7.1)
    pathway_dec = resolve_pathway(context)
    pathway = pathway_dec.recommended_pathway

    collaborator_called = None
    action_taken = {}
    user_response = ""

    # Step 3: Pathway Execution
    if pathway == "resolve":
        collaborator_called = "it_knowledge_agent"
        match = kb.search_knowledge_base(raw_query, context.issue.affected_service)
        if match and match["is_safe"]:
            action_taken = {
                "article_id": match["article_id"],
                "title": match["title"],
                "confidence": match["confidence"],
            }
            user_response = (
                f"I found a verified self-service solution for you:\n\n"
                f"**{match['title']}**\n"
                f"{match['fix_instructions']}\n\n"
                f"Please let me know if this resolves your issue, or if you need further assistance."
            )
        else:
            # Fallthrough to Escalate
            pathway = "escalate"
            collaborator_called = "incident_management_agent"

    if pathway == "request":
        collaborator_called = "service_request_agent"
        requested_item = context.issue.affected_service or "Requested Software/Hardware"
        elig_dec = evaluate_eligibility_and_approval(context, requested_item)

        req_res = iam.create_service_request(
            user_id=user_id,
            item_name=requested_item,
            justification=raw_query,
            approval_required=elig_dec.approval_required,
            approver_role=elig_dec.approver_role,
        )

        if not elig_dec.approval_required:
            iam.grant_access(user_id=user_id, item_name=requested_item)
            action_taken = {"request_id": req_res["request_id"], "status": "Auto-Provisioned"}
            user_response = (
                f"Your request for **{requested_item}** is pre-approved for your role ({context.user.role}). "
                f"Access has been automatically provisioned (Request #{req_res['request_id']}). You can start using it now!"
            )
        else:
            action_taken = {
                "request_id": req_res["request_id"],
                "status": "Pending Approval",
                "approver": elig_dec.approver_role,
                "is_privileged": elig_dec.is_privileged,
            }
            gate_type = "mandatory Security sign-off" if elig_dec.is_privileged else f"approval from your {elig_dec.approver_role}"
            user_response = (
                f"I've submitted Service Request #{req_res['request_id']} for **{requested_item}**. "
                f"Because this requires {gate_type}, it has been routed for Human-in-the-Loop review. "
                f"You will receive an email confirmation once decided."
            )

    if pathway == "escalate":
        collaborator_called = "incident_management_agent"
        # Deterministic Priority & Major Incident evaluation
        prio_dec = evaluate_priority(context)
        mi_dec = evaluate_major_incident(context)

        inc_res = itsm.create_or_update_incident(
            service=context.issue.affected_service or "General IT",
            user_id=user_id,
            priority=prio_dec.priority,
            description=raw_query,
            urgency=context.issue.stated_urgency,
            time_sensitivity_minutes=context.issue.time_sensitivity_minutes,
        )

        action_taken = {
            "incident_id": inc_res["incident_id"],
            "priority": prio_dec.priority,
            "sla_hours": prio_dec.response_sla_hours,
            "is_duplicate_merged": inc_res.get("is_duplicate_merged", False),
            "major_incident_candidate": mi_dec.major_incident_candidate,
        }

        # Format user response grounded in Policy Engine results
        if inc_res.get("is_duplicate_merged"):
            user_response = (
                f"This looks like a wider {context.issue.affected_service} issue affecting several team members right now. "
                f"I've attached you to the existing incident (**{inc_res['incident_id']}**, Priority: **{prio_dec.priority}**, "
                f"response SLA within {int(prio_dec.response_sla_hours)} hr). "
            )
            if context.issue.time_sensitivity_minutes:
                user_response += f"I have highlighted your meeting deadline in {context.issue.time_sensitivity_minutes} minutes as an urgent note for the responding engineer. "
            user_response += "I'll notify you as soon as updates are posted."
        else:
            sec_note = " (Flagged for Security Response)" if context.security_signal.flag else ""
            user_response = (
                f"I've opened Incident Ticket **{inc_res['incident_id']}**{sec_note} with priority **{prio_dec.priority}** "
                f"(expected response SLA: {prio_dec.response_sla_hours} hours). "
            )
            if mi_dec.major_incident_candidate:
                user_response += "Due to critical service impact, our on-call Major Incident Manager has been alerted for declaration review. "
            user_response += "An engineer has been dispatched to investigate."

    if pathway == "clarify":
        collaborator_called = "it_navigator_primary"
        user_response = (
            "Could you please specify which application or service is experiencing the issue, "
            "and any error message or behavior you're seeing?"
        )

    return {
        "query": raw_query,
        "context": context.model_dump(),
        "pathway_decision": pathway_dec.model_dump(),
        "collaborator": collaborator_called,
        "action_taken": action_taken,
        "response": user_response,
    }


def print_simulation(result: Dict[str, Any]):
    """Pretty-print execution results to terminal."""
    ctx = result["context"]
    pdec = result["pathway_decision"]

    print("\n" + "=" * 70)
    print(f"  EMPLOYEE QUERY: \"{result['query']}\"")
    print("=" * 70)
    print("  [SIGNAL EXTRACTION & CONTEXT]")
    print(f"    - User              : {ctx['user']['name']} ({ctx['user']['role']} - {ctx['user']['department']})")
    print(f"    - Affected Service  : {ctx['issue']['affected_service']} (Criticality: {ctx['service_context']['business_criticality']})")
    print(f"    - Service Health    : {ctx['service_context']['current_health_status']} ({ctx['service_context']['similar_reports_last_hour']} similar reports in last hr)")
    print(f"    - Security Signal   : Flag={ctx['security_signal']['flag']} (Category: {ctx['security_signal']['category']}, Conf: {ctx['security_signal']['confidence']})")
    print(f"    - Stated Urgency    : {ctx['issue']['stated_urgency']} (Time sensitivity: {ctx['issue']['time_sensitivity_minutes']} min)")

    print("\n  [DETERMINISTIC POLICY ENGINE]")
    print(f"    - Pathway Decision  : {pdec['recommended_pathway'].upper()} (Rule: {pdec['reasoning_code']})")
    if result["collaborator"]:
        print(f"    - Collaborator Agent: {result['collaborator']}")
    if result["action_taken"]:
        print(f"    - Action Output     : {json.dumps(result['action_taken'])}")

    print("\n  [NATURAL LANGUAGE RESPONSE]")
    print(f"    {result['response']}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IT Navigator Runner")
    parser.add_argument("--query", type=str, default="I can't access Salesforce and I have a client meeting in 20 minutes.", help="Employee problem description")
    args = parser.parse_args()

    res = execute_pipeline(args.query)
    print_simulation(res)
