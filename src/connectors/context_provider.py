"""Context Assembler Tool (Section 6 & 8.2 of Build Spec).
Assembles the complete Situation Object by unifying HR, CMDB, ITSM, and Security signals.
"""
import re
from typing import Optional, Dict, Any
from src.models.context import (
    UserContext,
    IssueContext,
    ServiceContext,
    PolicyContext,
    SituationContext,
)
from src.security.security_classifier import classify_security_risk
from src.connectors.mock_itsm import get_itsm_client
from src.connectors.mock_iam import get_iam_client
from src.connectors.mock_kb import get_kb_client


class ContextProvider:
    def __init__(self):
        self.itsm = get_itsm_client()
        self.iam = get_iam_client()
        self.kb = get_kb_client()

    def assemble_context(
        self,
        raw_text: str,
        user_id: str = "u12345",
        override_service: Optional[str] = None,
        override_urgency: Optional[str] = None,
        prior_resolve_attempted: bool = False,
    ) -> SituationContext:
        """Assembles the single unified Situation Object."""
        text = raw_text.strip()
        text_lower = text.lower()

        # 1. Detect service
        detected_service = override_service
        if not detected_service:
            known_services = ["Salesforce", "Workday", "GitHub", "Slack", "ExpenseApp", "Jira", "VPN", "Printer"]
            for svc in known_services:
                if svc.lower() in text_lower:
                    detected_service = svc
                    break

        # 2. Detect urgency & time sensitivity
        urgency = override_urgency or "medium"
        time_sensitivity = None

        time_match = re.search(r"(\d+)\s*(min|minute|minutes|hour|hours)", text_lower)
        if time_match:
            val = int(time_match.group(1))
            unit = time_match.group(2)
            time_sensitivity = val * 60 if "hour" in unit else val
            if time_sensitivity <= 60:
                urgency = "high"

        if any(w in text_lower for w in ["urgent", "asap", "emergency", "immediately", "deadline", "meeting in"]):
            urgency = "high"

        # 3. Detect intent
        intent = "general_inquiry"
        if any(w in text_lower for w in ["can't access", "cannot access", "unable to login", "login failed"]):
            intent = "access_login_issue"
        elif any(w in text_lower for w in ["broken", "error", "500", "crashed", "failing", "stopped working"]):
            intent = "break_fix"
        elif any(w in text_lower for w in ["need access to", "request access", "order", "license for", "permission to"]):
            intent = "software_request"
        elif any(w in text_lower for w in ["new laptop", "monitor", "keyboard", "hardware"]):
            intent = "hardware_request"
        elif any(w in text_lower for w in ["disconnect", "disconnecting", "slow"]):
            intent = "performance_degradation"

        issue_ctx = IssueContext(
            raw_text=text,
            detected_intent=intent,
            affected_service=detected_service,
            stated_urgency=urgency,
            time_sensitivity_minutes=time_sensitivity,
            prior_resolve_attempted=prior_resolve_attempted,
        )

        # 4. Fetch User Profile
        u_data = self.iam.get_user(user_id)
        user_ctx = UserContext(
            id=u_data["id"],
            name=u_data.get("name", "Employee"),
            department=u_data.get("department", "General"),
            role=u_data.get("role", "Employee"),
            location=u_data.get("location"),
            manager_id=u_data.get("manager_id"),
        )

        # 5. Fetch Service CMDB & Health Context
        svc_data = self.itsm.get_service_info(detected_service or "")
        open_incs = self.itsm.check_similar_incidents(detected_service or "")

        service_ctx = ServiceContext(
            business_criticality=svc_data.get("criticality", "Tier 3"),
            current_health_status=svc_data.get("health", "healthy"),
            known_open_incidents=len(open_incs),
            similar_reports_last_hour=svc_data.get("similar_reports_last_hour", 0),
        )

        # 6. Policy & Entitlements Context
        is_priv_intent = any(k in text_lower for k in ["admin", "root", "firewall", "production database", "privileged"])
        policy_ctx = PolicyContext(
            user_access_level=u_data.get("access_level", "standard"),
            existing_entitlements=u_data.get("entitlements", []),
            requires_privileged_flag=is_priv_intent,
        )

        # 7. Semantic Security Classifier (Layer 1 + Layer 2)
        sec_signal = classify_security_risk(text)

        # 8. KB Article Lookup
        kb_match = self.kb.search_knowledge_base(text, detected_service)
        kb_conf = kb_match["confidence"] if kb_match else 0.0
        kb_safe = kb_match["is_safe"] if kb_match else False
        kb_id = kb_match["article_id"] if kb_match else None

        return SituationContext(
            user=user_ctx,
            issue=issue_ctx,
            service_context=service_ctx,
            policy_context=policy_ctx,
            security_signal=sec_signal,
            kb_match_confidence=kb_conf,
            kb_match_is_safe=kb_safe,
            kb_match_article_id=kb_id,
        )


_context_provider_singleton = ContextProvider()


def get_context_provider() -> ContextProvider:
    return _context_provider_singleton
