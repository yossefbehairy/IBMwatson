"""Mock ITSM (ServiceNow / Jira Service Management) connector.
Handles incident creation, deduplication against active outages, and Major Incident declaration.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime


class MockITSMClient:
    def __init__(self):
        # Service CMDB registry
        self.services = {
            "Salesforce": {
                "criticality": "Tier 1",
                "health": "degraded",
                "similar_reports_last_hour": 3,
            },
            "Workday": {
                "criticality": "Tier 1",
                "health": "healthy",
                "similar_reports_last_hour": 0,
            },
            "GitHub": {
                "criticality": "Tier 1",
                "health": "healthy",
                "similar_reports_last_hour": 0,
            },
            "Slack": {
                "criticality": "Tier 1",
                "health": "healthy",
                "similar_reports_last_hour": 0,
            },
            "ExpenseApp": {
                "criticality": "Tier 2",
                "health": "degraded",
                "similar_reports_last_hour": 1,
            },
            "Jira": {
                "criticality": "Tier 2",
                "health": "healthy",
                "similar_reports_last_hour": 0,
            },
            "InternalWiki": {
                "criticality": "Tier 3",
                "health": "healthy",
                "similar_reports_last_hour": 0,
            },
            "Printer": {
                "criticality": "Tier 3",
                "health": "healthy",
                "similar_reports_last_hour": 0,
            },
        }

        # Active Incidents in ITSM
        self.incidents: Dict[str, Dict[str, Any]] = {
            "INC0004521": {
                "incident_id": "INC0004521",
                "service": "Salesforce",
                "title": "Salesforce login degradation and intermittent session timeouts",
                "priority": "P2",
                "status": "In Progress",
                "affected_users": ["u9981", "u7721", "u5543"],
                "created_at": "2026-09-07T22:30:00Z",
                "sla_hours": 1.0,
                "is_major_incident": False,
                "notes": [],
            }
        }
        self._next_inc_num = 5000

    def get_service_info(self, service_name: str) -> Dict[str, Any]:
        """Lookup CMDB information for a service."""
        for name, data in self.services.items():
            if name.lower() == (service_name or "").strip().lower():
                return data
        return {
            "criticality": "Tier 3",
            "health": "healthy",
            "similar_reports_last_hour": 0,
        }

    def check_similar_incidents(self, service_name: str) -> List[Dict[str, Any]]:
        """Return open incidents matching service for deduplication."""
        matches = []
        target = (service_name or "").strip().lower()
        for inc in self.incidents.values():
            if inc["service"].lower() == target and inc["status"] in ["Open", "In Progress"]:
                matches.append(inc)
        return matches

    def create_or_update_incident(
        self,
        service: str,
        user_id: str,
        priority: str,
        description: str,
        urgency: str = "medium",
        time_sensitivity_minutes: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Deduplicate against existing incident or create a new ticket."""
        similar = self.check_similar_incidents(service)
        if similar:
            existing = similar[0]
            if user_id not in existing["affected_users"]:
                existing["affected_users"].append(user_id)
            note = f"User {user_id} reported similar issue: {description}"
            if time_sensitivity_minutes:
                note += f" [Client deadline in {time_sensitivity_minutes} min]"
            existing["notes"].append(note)

            return {
                "action": "attached_to_existing",
                "incident_id": existing["incident_id"],
                "service": existing["service"],
                "priority": existing["priority"],
                "sla_hours": existing["sla_hours"],
                "affected_count": len(existing["affected_users"]),
                "is_duplicate_merged": True,
                "message": f"Added user {user_id} to existing incident {existing['incident_id']}.",
            }

        # Create new incident
        self._next_inc_num += 1
        new_id = f"INC000{self._next_inc_num}"
        sla = 1.0 if priority == "P2" else (0.25 if priority == "P1" else (4.0 if priority == "P3" else 24.0))

        new_inc = {
            "incident_id": new_id,
            "service": service,
            "title": description[:100],
            "priority": priority,
            "status": "Open",
            "affected_users": [user_id],
            "created_at": datetime.utcnow().isoformat(),
            "sla_hours": sla,
            "is_major_incident": False,
            "notes": [description],
        }
        self.incidents[new_id] = new_inc

        return {
            "action": "created_new",
            "incident_id": new_id,
            "service": service,
            "priority": priority,
            "sla_hours": sla,
            "affected_count": 1,
            "is_duplicate_merged": False,
            "message": f"Created new ticket {new_id} with priority {priority}.",
        }

    def declare_major_incident(self, incident_id: str, approver: str, notes: str = "") -> Dict[str, Any]:
        """HITL-gated declaration of Major Incident."""
        if incident_id in self.incidents:
            self.incidents[incident_id]["is_major_incident"] = True
            self.incidents[incident_id]["priority"] = "P1"
            self.incidents[incident_id]["major_incident_declared_by"] = approver
            self.incidents[incident_id]["major_incident_declared_at"] = datetime.utcnow().isoformat()
            return {
                "status": "declared",
                "incident_id": incident_id,
                "declared_by": approver,
                "success": True,
            }
        return {"status": "not_found", "incident_id": incident_id, "success": False}


# Singleton instance
_itsm_singleton = MockITSMClient()


def get_itsm_client() -> MockITSMClient:
    return _itsm_singleton
