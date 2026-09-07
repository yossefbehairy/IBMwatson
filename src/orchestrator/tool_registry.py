"""Tool Registry module (Section 8.2 of Build Spec).
Provides complete Watson Orchestrate tool registration payloads for all 12 tools.
"""
from typing import Dict, List, Any


def get_all_tool_definitions() -> List[Dict[str, Any]]:
    """Returns registration schemas for all 12 IT Navigator tools."""
    tools = [
        {
            "name": "get_context",
            "display_name": "Get Situation Context",
            "description": "Assembles structured situation context from HR directory, CMDB, ITSM, and monitoring.",
            "permission": "read_only",
            "input_schema": {
                "type": "object",
                "properties": {
                    "raw_text": {"type": "string", "description": "Original user issue description"},
                    "user_id": {"type": "string", "description": "Employee user ID, default u12345"},
                },
                "required": ["raw_text"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "user": {"type": "object"},
                    "issue": {"type": "object"},
                    "service_context": {"type": "object"},
                    "policy_context": {"type": "object"},
                    "security_signal": {"type": "object"},
                },
            },
            "binding": {
                "python": {
                    "function": "src.connectors.context_provider:get_context_provider().assemble_context",
                    "requirements": ["pydantic>=2.0"],
                }
            },
        },
        {
            "name": "classify_security_risk",
            "display_name": "Classify Security Risk",
            "description": "Two-layer semantic and fast pattern classifier to detect explicit or implicit security risks.",
            "permission": "read_only",
            "input_schema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Problem description text"},
                },
                "required": ["text"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "flag": {"type": "boolean"},
                    "confidence": {"type": "number"},
                    "category": {"type": "string"},
                },
                "required": ["flag"],
            },
            "binding": {
                "python": {
                    "function": "src.security.security_classifier:classify_security_risk",
                    "requirements": [],
                }
            },
        },
        {
            "name": "resolve_pathway",
            "display_name": "Resolve Pathway",
            "description": "Deterministic Pathway Resolver (Resolve / Request / Escalate / Clarify) per Section 7.1.",
            "permission": "read_only",
            "input_schema": {
                "type": "object",
                "properties": {
                    "context": {"type": "object", "description": "The full SituationContext object"},
                },
                "required": ["context"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "recommended_pathway": {"type": "string", "enum": ["resolve", "request", "escalate", "clarify"]},
                    "reasoning_code": {"type": "string"},
                    "missing_signal": {"type": "string"},
                },
                "required": ["recommended_pathway", "reasoning_code"],
            },
            "binding": {
                "python": {
                    "function": "src.policy_engine.pathway_resolver:resolve_pathway",
                    "requirements": ["pydantic>=2.0"],
                }
            },
        },
        {
            "name": "evaluate_priority",
            "display_name": "Evaluate Priority & SLA",
            "description": "Deterministic Priority Matrix (P1-P4) and SLA calculator per Section 7.2.",
            "permission": "read_only",
            "input_schema": {
                "type": "object",
                "properties": {
                    "context": {"type": "object", "description": "The full SituationContext object"},
                },
                "required": ["context"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "priority": {"type": "string", "enum": ["P1", "P2", "P3", "P4"]},
                    "response_sla_hours": {"type": "number"},
                    "resolution_sla_hours": {"type": "number"},
                    "reasoning_code": {"type": "string"},
                },
                "required": ["priority", "response_sla_hours"],
            },
            "binding": {
                "python": {
                    "function": "src.policy_engine.priority_engine:evaluate_priority",
                    "requirements": ["pydantic>=2.0"],
                }
            },
        },
        {
            "name": "evaluate_major_incident",
            "display_name": "Evaluate Major Incident",
            "description": "Deterministic criteria checker for Major Incident candidate status per Section 7.3.",
            "permission": "read_only",
            "input_schema": {
                "type": "object",
                "properties": {
                    "context": {"type": "object", "description": "The full SituationContext object"},
                },
                "required": ["context"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "major_incident_candidate": {"type": "boolean"},
                    "reasoning_code": {"type": "string"},
                    "requires_human_signoff": {"type": "boolean"},
                },
                "required": ["major_incident_candidate"],
            },
            "binding": {
                "python": {
                    "function": "src.policy_engine.major_incident_engine:evaluate_major_incident",
                    "requirements": ["pydantic>=2.0"],
                }
            },
        },
        {
            "name": "evaluate_eligibility_and_approval",
            "display_name": "Evaluate Access Eligibility & Approval",
            "description": "Deterministic access eligibility and HITL approval routing per Section 7.4.",
            "permission": "read_only",
            "input_schema": {
                "type": "object",
                "properties": {
                    "context": {"type": "object", "description": "The full SituationContext object"},
                    "requested_item": {"type": "string", "description": "Requested software/hardware name"},
                },
                "required": ["context"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "is_eligible": {"type": "boolean"},
                    "approval_required": {"type": "boolean"},
                    "approver_role": {"type": "string"},
                    "is_privileged": {"type": "boolean"},
                    "reasoning_code": {"type": "string"},
                },
                "required": ["is_eligible", "approval_required"],
            },
            "binding": {
                "python": {
                    "function": "src.policy_engine.eligibility_engine:evaluate_eligibility_and_approval",
                    "requirements": ["pydantic>=2.0"],
                }
            },
        },
        {
            "name": "check_similar_incidents",
            "display_name": "Check Similar Incidents",
            "description": "Queries ITSM to find open incidents matching service to deduplicate issues.",
            "permission": "read_only",
            "input_schema": {
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Service name to check in ITSM"},
                },
                "required": ["service_name"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "incidents": {"type": "array"},
                },
            },
            "binding": {
                "python": {
                    "function": "src.connectors.mock_itsm:get_itsm_client().check_similar_incidents",
                    "requirements": [],
                }
            },
        },
        {
            "name": "search_knowledge_base",
            "display_name": "Search IT Knowledge Base",
            "description": "Searches verified IT runbooks for safe self-service candidate fixes.",
            "permission": "read_only",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Issue description"},
                    "service": {"type": "string", "description": "Optional affected service filter"},
                },
                "required": ["query"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "article_id": {"type": "string"},
                    "title": {"type": "string"},
                    "fix_instructions": {"type": "string"},
                    "is_safe": {"type": "boolean"},
                    "confidence": {"type": "number"},
                },
            },
            "binding": {
                "python": {
                    "function": "src.connectors.mock_kb:get_kb_client().search_knowledge_base",
                    "requirements": [],
                }
            },
        },
        {
            "name": "create_or_update_incident",
            "display_name": "Create or Update Incident",
            "description": "Creates an incident in ITSM or deduplicates by attaching user to an existing ticket.",
            "permission": "read_write",
            "input_schema": {
                "type": "object",
                "properties": {
                    "service": {"type": "string", "description": "Affected application"},
                    "user_id": {"type": "string", "description": "Reporting user ID"},
                    "priority": {"type": "string", "description": "Priority P1-P4"},
                    "description": {"type": "string", "description": "Problem summary"},
                    "urgency": {"type": "string", "description": "Stated urgency"},
                    "time_sensitivity_minutes": {"type": "integer", "description": "Deadline in minutes"},
                },
                "required": ["service", "user_id", "priority", "description"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "incident_id": {"type": "string"},
                    "priority": {"type": "string"},
                    "sla_hours": {"type": "number"},
                    "is_duplicate_merged": {"type": "boolean"},
                },
            },
            "binding": {
                "python": {
                    "function": "src.connectors.mock_itsm:get_itsm_client().create_or_update_incident",
                    "requirements": [],
                }
            },
        },
        {
            "name": "create_service_request",
            "display_name": "Create Service Request",
            "description": "Registers a service request for software, access, or hardware in IAM/catalog.",
            "permission": "read_write",
            "input_schema": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Requesting employee ID"},
                    "item_name": {"type": "string", "description": "Catalog item name"},
                    "justification": {"type": "string", "description": "Business justification"},
                    "approval_required": {"type": "boolean"},
                    "approver_role": {"type": "string"},
                },
                "required": ["user_id", "item_name", "justification"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "request_id": {"type": "string"},
                    "status": {"type": "string"},
                    "requires_hitl": {"type": "boolean"},
                },
            },
            "binding": {
                "python": {
                    "function": "src.connectors.mock_iam:get_iam_client().create_service_request",
                    "requirements": [],
                }
            },
        },
        {
            "name": "grant_access",
            "display_name": "Grant Access (HITL Gated)",
            "description": "Provisions access. Privileged entitlements require mandatory human approval.",
            "permission": "read_write",
            "input_schema": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "item_name": {"type": "string"},
                    "approver": {"type": "string"},
                    "is_privileged": {"type": "boolean"},
                },
                "required": ["user_id", "item_name"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "granted": {"type": "boolean"},
                },
            },
            "binding": {
                "python": {
                    "function": "src.connectors.mock_iam:get_iam_client().grant_access",
                    "requirements": [],
                }
            },
        },
        {
            "name": "declare_major_incident",
            "display_name": "Declare Major Incident (HITL Sign-Off)",
            "description": "Formally declares a Major Incident. Always requires human sign-off (MIM on-call).",
            "permission": "read_write",
            "input_schema": {
                "type": "object",
                "properties": {
                    "incident_id": {"type": "string"},
                    "approver": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["incident_id", "approver"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "incident_id": {"type": "string"},
                    "success": {"type": "boolean"},
                },
            },
            "binding": {
                "python": {
                    "function": "src.connectors.mock_itsm:get_itsm_client().declare_major_incident",
                    "requirements": [],
                }
            },
        },
    ]
    return tools
