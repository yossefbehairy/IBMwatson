"""Mock IAM & Identity Governance connector.
Handles user profile lookup, role entitlements, service requests, and HITL access granting.
"""
from typing import Dict, Any, Optional
from datetime import datetime


class MockIAMClient:
    def __init__(self):
        # HR User Directory
        self.users: Dict[str, Dict[str, Any]] = {
            "u12345": {
                "id": "u12345",
                "name": "Sarah Connor",
                "department": "Sales",
                "role": "Account Executive",
                "location": "Cairo",
                "manager_id": "u10021",
                "access_level": "standard",
                "entitlements": ["Salesforce - Standard User", "Slack - Standard"],
            },
            "u23456": {
                "id": "u23456",
                "name": "Alex Murphy",
                "department": "Engineering",
                "role": "Software Engineer",
                "location": "London",
                "manager_id": "u10022",
                "access_level": "standard",
                "entitlements": ["GitHub - Developer", "Slack - Standard"],
            },
            "u34567": {
                "id": "u34567",
                "name": "John Doe",
                "department": "Finance",
                "role": "Financial Analyst",
                "location": "New York",
                "manager_id": "u10023",
                "access_level": "standard",
                "entitlements": ["Workday - Core"],
            },
        }

        # Service Requests ledger
        self.requests: Dict[str, Dict[str, Any]] = {}
        self._next_req_num = 1000

    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Fetch user HR and identity profile."""
        return self.users.get(
            user_id,
            {
                "id": user_id,
                "name": "Unknown User",
                "department": "General",
                "role": "Employee",
                "location": "Remote",
                "manager_id": "u10000",
                "access_level": "standard",
                "entitlements": [],
            },
        )

    def create_service_request(
        self,
        user_id: str,
        item_name: str,
        justification: str,
        approval_required: bool,
        approver_role: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Open a service catalog request."""
        self._next_req_num += 1
        req_id = f"REQ000{self._next_req_num}"
        status = "Pending Approval" if approval_required else "Auto-Approved"

        record = {
            "request_id": req_id,
            "user_id": user_id,
            "item_name": item_name,
            "justification": justification,
            "status": status,
            "approval_required": approval_required,
            "approver_role": approver_role,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.requests[req_id] = record

        return {
            "request_id": req_id,
            "item_name": item_name,
            "status": status,
            "requires_hitl": approval_required,
            "approver_role": approver_role,
            "message": f"Service request {req_id} registered with status: {status}.",
        }

    def grant_access(
        self,
        user_id: str,
        item_name: str,
        approver: Optional[str] = None,
        is_privileged: bool = False,
    ) -> Dict[str, Any]:
        """Execute access provisioning. Enforces HITL check if privileged."""
        user = self.get_user(user_id)
        if is_privileged and not approver:
            return {
                "status": "blocked",
                "message": "Privileged access cannot be granted without explicit human approver.",
                "granted": False,
            }

        if item_name not in user["entitlements"]:
            user["entitlements"].append(item_name)

        return {
            "status": "granted",
            "user_id": user_id,
            "item_name": item_name,
            "granted_by": approver or "system_auto_provision",
            "granted": True,
            "timestamp": datetime.utcnow().isoformat(),
        }


# Singleton instance
_iam_singleton = MockIAMClient()


def get_iam_client() -> MockIAMClient:
    return _iam_singleton
