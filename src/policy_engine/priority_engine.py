"""Priority Engine module (Section 7.2 & 7.5 of Build Spec).
Computes deterministic Incident Priority (P1-P4) and SLAs.
"""
from typing import Tuple
from src.models.context import SituationContext
from src.models.decisions import PriorityDecision

# SLA Table: (response_sla_hours, resolution_sla_hours)
SLA_TABLE = {
    "P1": (0.25, 4.0),       # 15 min response, 4 hours resolution
    "P2": (1.0, 8.0),        # 1 hour response, 8 hours resolution
    "P3": (4.0, 48.0),       # 4 hours response, 2 business days (48 hrs)
    "P4": (24.0, 120.0),     # 1 business day response, 5 business days (120 hrs)
}


def evaluate_priority(context: SituationContext) -> PriorityDecision:
    """Computes deterministic priority and SLA based on:
    Business Criticality x Users Affected x Stated Urgency
    """
    criticality = (context.service_context.business_criticality or "Tier 3").strip()
    similar_reports = context.service_context.similar_reports_last_hour
    urgency = (context.issue.stated_urgency or "medium").strip().lower()

    # Determine whether blast radius is multiple or single
    is_multiple_users = similar_reports >= 2
    is_high_urgency = urgency in ["high", "critical"]

    priority = "P4"
    reasoning_code = "DEFAULT_LOW_PRIORITY"

    if criticality == "Tier 1":
        if is_multiple_users and is_high_urgency:
            priority = "P1"
            reasoning_code = "TIER1_MULTIPLE_USERS_HIGH_URGENCY"
        elif not is_multiple_users and is_high_urgency:
            priority = "P2"
            reasoning_code = "TIER1_SINGLE_USER_HIGH_URGENCY"
        else:
            priority = "P3"
            reasoning_code = "TIER1_LOW_MEDIUM_URGENCY"

    elif criticality == "Tier 2":
        if is_multiple_users and is_high_urgency:
            priority = "P2"
            reasoning_code = "TIER2_MULTIPLE_USERS_HIGH_URGENCY"
        elif not is_multiple_users:
            priority = "P3"
            reasoning_code = "TIER2_SINGLE_USER"
        else:
            priority = "P3"
            reasoning_code = "TIER2_MULTIPLE_USERS_MODERATE_URGENCY"

    else:  # Tier 3 or internal back-office
        priority = "P4"
        reasoning_code = "TIER3_INTERNAL_SERVICE"

    resp_sla, res_sla = SLA_TABLE.get(priority, (24.0, 120.0))

    return PriorityDecision(
        priority=priority,
        response_sla_hours=resp_sla,
        resolution_sla_hours=res_sla,
        reasoning_code=reasoning_code,
    )
