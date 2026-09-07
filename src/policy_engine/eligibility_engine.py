"""Eligibility & Approval Engine module (Section 7.4 of Build Spec).
Evaluates access eligibility, approval necessity, and approver role.
Enforces mandatory Human-in-the-Loop for privileged access and security exceptions.
"""
from typing import Dict, Set
from src.models.context import SituationContext
from src.models.decisions import EligibilityDecision

# Standard baseline entitlements pre-approved by role
ROLE_ENTITLEMENT_CATALOG: Dict[str, Set[str]] = {
    "Account Executive": {
        "Salesforce - Standard User",
        "Slack - Standard",
        "Google Workspace",
        "Zoom Basic",
        "DocuSign Viewer",
    },
    "Software Engineer": {
        "GitHub - Developer",
        "Slack - Standard",
        "Google Workspace",
        "Jira - Developer",
        "AWS Sandbox",
    },
    "Data Analyst": {
        "Tableau - Creator",
        "Snowflake - ReadOnly",
        "Google Workspace",
        "Slack - Standard",
    },
    "HR Specialist": {
        "Workday - Core",
        "Google Workspace",
        "Slack - Standard",
    },
}

# Privileged items and security exceptions that ALWAYS require IT Security approval
PRIVILEGED_ENTITLEMENTS = {
    "AWS Production Admin",
    "Production Database Write",
    "Domain Admin",
    "Kubernetes Cluster Admin",
    "SSH Root Access",
    "Firewall Rule Exception",
    "Temporary Local Admin",
    "Security Scanner Bypass",
}

HARDWARE_CATALOG = {
    "Laptop Refresh",
    "Secondary Monitor",
    "Ergonomic Keyboard",
    "Headset",
}


def evaluate_eligibility_and_approval(
    context: SituationContext,
    requested_item: str = "",
) -> EligibilityDecision:
    """Consumes user context and requested item to compute eligibility and approval gates."""
    user = context.user
    role = user.role or "Employee"
    user_access_level = (context.policy_context.user_access_level or "standard").lower()

    target_item = requested_item or context.issue.affected_service or ""
    raw_lower = context.issue.raw_text.lower()

    # 1. Privileged Access & Security Exceptions (Mandatory HITL -> IT Security)
    is_privileged = (
        context.policy_context.requires_privileged_flag
        or any(priv.lower() in target_item.lower() or priv.lower() in raw_lower for priv in PRIVILEGED_ENTITLEMENTS)
        or any(k in raw_lower for k in ["root access", "admin rights", "firewall rule", "temp admin", "sudo access", "privileged"])
    )

    if is_privileged:
        return EligibilityDecision(
            is_eligible=True,
            approval_required=True,
            approver_role="IT Security",
            is_privileged=True,
            reasoning_code="PRIVILEGED_ACCESS_MANDATORY_HITL",
        )

    # 2. Hardware Requests (Requires Line Manager Approval)
    is_hardware = (
        any(hw.lower() in target_item.lower() or hw.lower() in raw_lower for hw in HARDWARE_CATALOG)
        or any(k in raw_lower for k in ["laptop", "monitor", "hardware", "keyboard", "mouse", "headset"])
    )

    if is_hardware:
        return EligibilityDecision(
            is_eligible=True,
            approval_required=True,
            approver_role="Line manager",
            is_privileged=False,
            reasoning_code="HARDWARE_REQUEST_LINE_MANAGER_APPROVAL",
        )

    # 3. Standard Pre-Approved Software Entitlements
    approved_for_role = ROLE_ENTITLEMENT_CATALOG.get(role, set())
    is_standard_approved = any(
        ent.lower() in target_item.lower() or target_item.lower() in ent.lower()
        for ent in approved_for_role
    )

    if is_standard_approved:
        return EligibilityDecision(
            is_eligible=True,
            approval_required=False,
            approver_role=None,
            is_privileged=False,
            reasoning_code="ROLE_PREAPPROVED_AUTO_PROVISION",
        )

    # 4. Non-Standard Software / License Requests (Requires Line Manager Approval)
    return EligibilityDecision(
        is_eligible=True,
        approval_required=True,
        approver_role="Line manager",
        is_privileged=False,
        reasoning_code="NON_STANDARD_ACCESS_MANAGER_APPROVAL_REQUIRED",
    )
