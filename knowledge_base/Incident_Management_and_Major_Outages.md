# Enterprise Incident Management - Priority Matrix & Major Outages

---

## Active Known Major Incidents (Deduplication)
- **Incident Number**: **INC0004521**
- **Affected Core Service**: **Salesforce CRM**
- **Current Status**: Active Major Outage (P1 - Critical)
- **Impact Scope**: Global (All Sales, Marketing, and Customer Support users)
- **Root Cause**: Cloud provider region gateway timeout and SSO token validation degradation.
- **Assigned Response Teams**: Cloud Engineering Operations + Salesforce Premier Support Command.
- **SLA Target for Next Communication**: 15 minutes.
- **Deduplication Directive**:
  - Any new report concerning Salesforce unavailability, login loops, or CRM timeouts MUST be linked directly to INC0004521.
  - DO NOT generate duplicate incident tickets.

---

## Deterministic Incident Priority Matrix (P1 - P4)

| Priority Level | Classification | Criteria | Target Response SLA | Escalation Target |
|---|---|---|---|---|
| **P1** | **Critical** | Company-wide revenue outage, core ERP/CRM down, or VIP/Executive work blockage | 15 Minutes | Major Incident Commander + SecOps Lead |
| **P2** | **High** | Critical departmental system unavailable with no workaround, or severe performance degradation | 1 Hour | Senior Tier-2 Systems Engineer |
| **P3** | **Medium** | Partial service degradation, non-blocking software bugs, single-user standard issue | 4 Hours | Service Desk Queue |
| **P4** | **Low** | Cosmetic glitches, general inquiries, minor peripheral defects | 24 Hours | Backlog / General Support |

---

## Security Incident Protocols
- Any detection of ransomware indicators, phishing attacks, credential compromise, or unexpected mass file encryption triggers an automatic priority elevation to **P1 Security Incident**.
- Response: Immediate endpoint network isolation advisory and paging of 24/7 SecOps on-call team.
