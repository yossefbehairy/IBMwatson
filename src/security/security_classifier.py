"""Two-Layer Security Classifier (Section 5.4 & 8.2 of Build Spec).
Combines:
1. Fast Deterministic Keyword/Regex Guardrail (Zero-latency floor)
2. Semantic Security Risk Pattern Detector (Fail-safe biased)
"""
import re
from typing import Dict, Any, Tuple
from src.models.context import SecuritySignal

# Layer 1: Fast explicit keyword / regex patterns
EXPLICIT_PATTERNS = [
    (r"\b(hacked|hacker|hacking)\b", "explicit_compromise"),
    (r"\b(phish|phishing|spear-phishing)\b", "phishing_threat"),
    (r"\b(ransomware|malware|keylogger|trojan)\b", "malware_infection"),
    (r"\b(breach|data breach|data exfiltration)\b", "data_breach"),
    (r"\b(unauthorized access|unauthorized user)\b", "unauthorized_access"),
    (r"\b(credential leak|dumped passwords|password leak)\b", "credential_leak"),
    (r"\b(compromised account|account compromised)\b", "account_compromise"),
]


def classify_security_risk(text: str) -> SecuritySignal:
    """Evaluates input text through the 2-layer security model.
    Fail-safe biased: defaults to flag=True when uncertainty or risk pattern detected.
    """
    if not text or not text.strip():
        return SecuritySignal(flag=False, confidence=0.0, category=None)

    clean_text = text.strip().lower()

    # --- Layer 1: Fast Explicit Guardrail ---
    for pattern, cat in EXPLICIT_PATTERNS:
        if re.search(pattern, clean_text):
            return SecuritySignal(
                flag=True,
                confidence=1.0,
                category=cat,
            )

    # --- Layer 2: Semantic Implicit Pattern Detector ---
    # 1. Unexpected Data Exposure / Cross-User Leakage
    has_perception = bool(re.search(r"\b(seeing|see|shows|displaying|displays|viewing|view|shows up|contains?)\b", clean_text))
    has_cross_target = bool(re.search(r"\b(another|someone else's?|other employees?'?|a colleague's?'?|different user's?'?|confidential|sensitive)\b", clean_text))
    has_sensitive_data = bool(re.search(r"\b(client|clients|salary|bonus|payroll|records?|contracts?|data|documents?|files?|ssn|credit card|credit cards)\b", clean_text))

    if (has_perception and has_cross_target and has_sensitive_data) or "data i shouldn't have access to" in clean_text or "data i should not have access to" in clean_text:
        return SecuritySignal(
            flag=True,
            confidence=0.95,
            category="unexpected_data_exposure",
        )

    # 2. Session Hijacking / Identity Confusion
    if re.search(r"\b(logged me in as|logging in as|switched to)\s+(someone else|another|different)", clean_text) or \
       (re.search(r"\b(profile|account)\b", clean_text) and re.search(r"\b(displays?|shows?|has)\b", clean_text) and re.search(r"\b(different|someone else's?|wrong)\b", clean_text)):
        return SecuritySignal(
            flag=True,
            confidence=0.96,
            category="session_hijacking_or_identity_confusion",
        )

    # 3. MFA / Unsolicited Authenticator Anomaly
    if re.search(r"\b(2fa|mfa|otp|one-time|push notification)\b", clean_text) and \
       re.search(r"\b(prompt|code|request|notification)\b", clean_text) and \
       re.search(r"\b(didn't|did not|unexpected|without logging|not try|out of the blue)\b", clean_text):
        return SecuritySignal(
            flag=True,
            confidence=0.95,
            category="credential_stuffing_or_unsolicited_mfa",
        )

    # 4. Credential Harvesting / Phishy Popup / Request for Codes
    if (re.search(r"\b(asking for|asked for|requesting|demanding)\b", clean_text) or re.search(r"\b(popup|pop-up)\s+(is\s+)?asking\b", clean_text)) and \
       re.search(r"\b(password|windows password|2fa|otp|pin|verification code|one-time|login code)\b", clean_text):
        return SecuritySignal(
            flag=True,
            confidence=0.94,
            category="credential_harvesting_attempt",
        )

    # 5. Unexplained Privilege Escalation
    if re.search(r"\b(administrator rights|admin rights|admin buttons|delete buttons|root access|super-user|elevated rights)\b", clean_text) and \
       re.search(r"\b(suddenly|overnight|unexpectedly|now have|now seeing)\b", clean_text):
        return SecuritySignal(
            flag=True,
            confidence=0.93,
            category="unexplained_privilege_escalation",
        )

    # 6. Unencrypted / Exposed Sensitive Financial / PII Data
    if re.search(r"\b(credit cards?|ssn|social security|passwords?)\b", clean_text) and \
       re.search(r"\b(unencrypted|plain text|clear text|exposed|publicly visible|leak|export contains)\b", clean_text):
        return SecuritySignal(
            flag=True,
            confidence=0.95,
            category="data_exposure_spill",
        )

    # 7. Ambient / Borderline fail-safe check
    ambiguous_triggers = [
        "shouldn't have access",
        "should not have access",
        "not my account",
        "somebody else's files",
        "someone else's documents",
        "weird login",
        "unrecognized device",
    ]
    if any(trig in clean_text for trig in ambiguous_triggers):
        return SecuritySignal(
            flag=True,
            confidence=0.80,
            category="ambiguous_security_anomaly",
        )

    # Clean / Benign interaction
    return SecuritySignal(
        flag=False,
        confidence=0.05,
        category=None,
    )
