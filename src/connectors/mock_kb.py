"""Mock IT Knowledge Base connector (Section 5.1 & 8.4 of Build Spec).
Provides semantic keyword lookup over verified IT runbooks with safety classification.
"""
from typing import Dict, List, Optional, Any


class MockKBClient:
    def __init__(self):
        self.articles = [
            {
                "id": "KB001",
                "title": "VPN Disconnecting or Failing to Reconnect",
                "service": "VPN",
                "keywords": ["vpn", "disconnect", "disconnecting", "anyconnect", "reconnect", "tunnel"],
                "fix_instructions": (
                    "1. Open Cisco AnyConnect.\n"
                    "2. Click 'Disconnect' and quit the application.\n"
                    "3. In Settings > Network, disable and re-enable Wi-Fi.\n"
                    "4. Re-open AnyConnect, select gateway 'vpn.company.com', and authenticate."
                ),
                "is_safe": True,
                "confidence": 0.92,
            },
            {
                "id": "KB002",
                "title": "Clearing Browser Cookies & Cache for Single Sign-On (SSO)",
                "service": "SSO",
                "keywords": ["sso", "login loop", "cookies", "cache", "browser", "okta"],
                "fix_instructions": (
                    "1. Press Ctrl+Shift+Delete in Chrome/Edge.\n"
                    "2. Select 'Cookies and other site data' for 'All time'.\n"
                    "3. Click 'Clear data' and relaunch the browser."
                ),
                "is_safe": True,
                "confidence": 0.88,
            },
            {
                "id": "KB003",
                "title": "Restarting Windows Local Print Spooler",
                "service": "Printer",
                "keywords": ["printer", "print spooler", "spooler", "stuck print", "printing"],
                "fix_instructions": (
                    "1. Open Windows Services (services.msc).\n"
                    "2. Right-click 'Print Spooler' and select 'Restart'.\n"
                    "3. Re-send your document to the printer queue."
                ),
                "is_safe": True,
                "confidence": 0.85,
            },
            {
                "id": "KB004",
                "title": "Self-Service Password Reset Portal",
                "service": "Identity",
                "keywords": ["password reset", "forgot password", "reset my password", "change password"],
                "fix_instructions": (
                    "1. Navigate to https://verify.company.com/self-service-reset.\n"
                    "2. Enter your employee ID and complete SMS 2FA verification.\n"
                    "3. Set your new compliant password."
                ),
                "is_safe": True,
                "confidence": 0.90,
            },
            {
                "id": "KB005",
                "title": "Modify Core Firewall Port Forwarding Rules",
                "service": "Network",
                "keywords": ["firewall", "port forwarding", "security rule", "open port"],
                "fix_instructions": "Requires modifying perimeter gateway rules.",
                "is_safe": False,  # Dangerous / Security impact! Must not self-resolve!
                "confidence": 0.95,
            },
        ]

    def search_knowledge_base(self, query: str, service: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Search runbooks for matching queries. Returns highest-scoring candidate if any."""
        q_lower = (query or "").lower()
        svc_lower = (service or "").lower()

        best_match = None
        best_score = 0.0

        for art in self.articles:
            score = 0.0
            # Service match bonus
            if svc_lower and svc_lower in art["service"].lower():
                score += 0.4

            # Keyword match
            matched_keywords = sum(1 for kw in art["keywords"] if kw in q_lower)
            if matched_keywords > 0:
                score += min(0.6, matched_keywords * 0.25)

            if score > best_score and score >= 0.5:
                best_score = score
                best_match = {
                    "article_id": art["id"],
                    "title": art["title"],
                    "service": art["service"],
                    "fix_instructions": art["fix_instructions"],
                    "is_safe": art["is_safe"],
                    "confidence": min(0.98, art["confidence"] * (score / 0.8)),
                }

        return best_match


# Singleton instance
_kb_singleton = MockKBClient()


def get_kb_client() -> MockKBClient:
    return _kb_singleton
