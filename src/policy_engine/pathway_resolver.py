"""Pathway Resolver module (Section 7.1 of Build Spec).
Deterministic routing between Resolve, Request, Escalate, and Clarify.
"""
from src.models.context import SituationContext
from src.models.decisions import PathwayDecision

PROVISIONING_INTENTS = {
    "software_request",
    "hardware_request",
    "access_request",
    "permission_request",
    "license_request",
    "provisioning",
    "request_new_access",
    "catalog_order",
}

BREAK_FIX_INTENTS = {
    "break_fix",
    "bug_error",
    "crash_issue",
    "outage",
    "performance_degradation",
    "access_login_issue",
    "hardware_failure",
}


def resolve_pathway(context: SituationContext) -> PathwayDecision:
    """Consumes structured context signals and returns the authoritative recommended pathway."""
    issue = context.issue
    sec = context.security_signal
    svc = context.service_context

    # 1. Unconditional Security Override: security_signal.flag = True -> Escalate
    if sec.flag:
        return PathwayDecision(
            recommended_pathway="escalate",
            reasoning_code="SECURITY_SIGNAL_ACTIVE",
            missing_signal=None,
        )

    # 2. Prior Resolve Failed Override: Never trap the user in a failed loop
    if issue.prior_resolve_attempted:
        return PathwayDecision(
            recommended_pathway="escalate",
            reasoning_code="PRIOR_RESOLVE_FAILED",
            missing_signal=None,
        )

    # 3. Wider Outage / Degraded Service Cluster Override:
    # If service is degraded or down, or there are multiple similar reports, do not attempt individual resolve
    if svc.current_health_status in ["degraded", "down"] or svc.similar_reports_last_hour >= 2:
        # If it's a break-fix or access error during outage, escalate
        if issue.detected_intent in BREAK_FIX_INTENTS or "access" in issue.detected_intent or "login" in issue.detected_intent:
            return PathwayDecision(
                recommended_pathway="escalate",
                reasoning_code="SERVICE_OUTAGE_OR_CLUSTER",
                missing_signal=None,
            )

    # 4. Safe Knowledge Base Self-Service Fix Available
    if context.kb_match_confidence >= 0.70 and context.kb_match_is_safe:
        return PathwayDecision(
            recommended_pathway="resolve",
            reasoning_code="SAFE_KB_MATCH_AVAILABLE",
            missing_signal=None,
        )

    # 5. Service Provisioning / Catalog Request Intent
    raw_lower = issue.raw_text.lower()
    is_provisioning = (
        issue.detected_intent in PROVISIONING_INTENTS
        or any(k in raw_lower for k in ["need access to", "request access", "order new", "new laptop", "provision license", "need permission for"])
    ) and not any(k in raw_lower for k in ["can't access", "cannot access", "stopped working", "broken", "throwing error", "down"])

    if is_provisioning:
        return PathwayDecision(
            recommended_pathway="request",
            reasoning_code="PROVISIONING_REQUEST_DETECTED",
            missing_signal=None,
        )

    # 6. Ambiguous Cases Check: If the problem is too vague to determine service or error
    if not issue.affected_service or issue.detected_intent in ["vague_issue", "general_inquiry", "clarify"]:
        if len(raw_lower.strip().split()) < 4 or any(k in raw_lower for k in ["being weird", "not working", "acting up", "something is wrong"]) and not issue.affected_service:
            return PathwayDecision(
                recommended_pathway="clarify",
                reasoning_code="AMBIGUOUS_SIGNAL_NEEDS_CLARIFICATION",
                missing_signal="affected_service_or_error_details",
            )

    # 7. Unserviceable Break/Fix: Default to Escalate
    return PathwayDecision(
        recommended_pathway="escalate",
        reasoning_code="UNSERVICEABLE_BREAK_FIX",
        missing_signal=None,
    )
