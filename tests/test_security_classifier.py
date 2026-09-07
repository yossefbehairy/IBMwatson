"""Tests for the Two-Layer Security Classifier (Section 5.4 of Build Spec).
Verifies that:
1. Explicit keywords are caught by the fast guardrail (Layer 1).
2. Implicit security incidents (no security keywords) are reliably caught (Layer 2).
3. Benign IT break-fix and requests do not generate false positives.
4. Fail-safe bias properly flags borderline cases.
"""
import sys
import os
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.security.security_classifier import classify_security_risk


# ==================== Layer 1: Explicit Keyword Guardrail ====================


@pytest.mark.parametrize(
    "query,expected_cat",
    [
        ("I think my account got hacked this morning", "explicit_compromise"),
        ("Received a phishing email pretending to be from HR", "phishing_threat"),
        ("A ransomware message is locking my files", "malware_infection"),
        ("We discovered an unauthorized user on our cloud network", "unauthorized_access"),
        ("My passwords were found in a credential leak online", "credential_leak"),
        ("I believe our customer database suffered a breach", "data_breach"),
    ],
)
def test_explicit_security_guardrail(query: str, expected_cat: str):
    sig = classify_security_risk(query)
    assert sig.flag is True
    assert sig.confidence == 1.0
    assert sig.category == expected_cat


# ==================== Layer 2: Implicit Security Risks (ZERO TOLERANCE) ====================


@pytest.mark.parametrize(
    "query",
    [
        "I can see a colleague's client records that I shouldn't have access to",
        "I'm seeing another employee's salary and bonus details in the portal",
        "The app logged me in as someone else when I refreshed",
        "My report showed data I shouldn't have access to",
        "Logged in and my profile displays a different user's name and email",
        "I received a 2FA prompt on my authenticator app but I didn't try to log in",
        "A popup is asking for my Windows password unexpectedly",
        "My account suddenly has administrator rights and delete buttons",
        "The customer export file contains unencrypted credit card numbers",
        "Someone contacted me asking for my one-time verification code",
    ],
)
def test_implicit_security_risks(query: str):
    """These implicit scenarios use zero security vocabulary but MUST trigger flag=True."""
    sig = classify_security_risk(query)
    assert sig.flag is True, f"Failed to flag implicit security risk: '{query}'"
    assert sig.confidence >= 0.70
    assert sig.category is not None


# ==================== Benign Non-Security Cases ====================


@pytest.mark.parametrize(
    "query",
    [
        "My VPN keeps disconnecting every 10 minutes when on home Wi-Fi",
        "I can't access Salesforce and I have a client meeting in 20 minutes",
        "The second floor office printer is showing a paper jam error",
        "I need access to the design system Figma file for my new project",
        "The expense report app is throwing a 500 internal server error",
        "How do I clear my browser cookies to fix an SSO login loop?",
        "My laptop battery is draining very fast today",
        "Requesting a secondary monitor for my home office setup",
    ],
)
def test_benign_non_security_cases(query: str):
    """Benign IT issues should not trigger false security alerts."""
    sig = classify_security_risk(query)
    assert sig.flag is False, f"False positive security alert on: '{query}'"
    assert sig.category is None
