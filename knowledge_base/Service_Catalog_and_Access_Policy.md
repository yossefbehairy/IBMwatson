# Enterprise IT Support - Service Catalog & Access Governance

This document defines standard software catalog tiers, eligibility rules, and human-in-the-loop approval workflows.

---

## Tier 1: Standard Self-Service Catalog (Auto-Approved)
- **Eligibility**: All full-time employees, contractors, and interns.
- **Approval Required**: No (Zero human touch).
- **Approved Applications**:
  1. **Miro Standard**: Whiteboarding and diagramming tool.
  2. **Figma Viewer**: Read-only design inspection license.
  3. **Notion Standard**: Internal documentation workspace.
  4. **Zoom Pro License**: Standard employee meeting license.
  5. **Grammarly Business Basic**: Writing assistant.
- **Fulfillment SLA**: Instant (< 2 minutes via automated SCIM/Okta provisioning).

---

## Tier 2: Departmental & Paid Licenses (Manager Approval Required)
- **Eligibility**: Requires direct budget holder and line-manager approval.
- **Applications & Hardware**:
  1. **Figma Editor License**: $45/month chargeback to cost center.
  2. **GitHub Copilot Enterprise**: For verified software engineers.
  3. **Docker Desktop Pro**: For development engineering staff.
  4. **Datadog Read-Only Dashboard**: For DevOps / SRE engineers.
  5. **Additional 27-inch 4K Monitor**: Ergonomic equipment request.
- **Workflow**:
  - System generates ticket (e.g. SR-10294) in `Pending Manager Approval`.
  - Automated Slack / Email notification dispatched to line manager.
  - Provisioning triggered immediately upon manager digital sign-off.

---

## Tier 3: Privileged & Elevated Security Access (Strict Human-in-the-Loop)
- **Policy**: STRICT ZERO TRUST. System or automated AI agents are strictly forbidden from self-granting privileged access.
- **Restricted Targets**:
  1. **AWS Production Root / IAM Administrator**
  2. **GCP Cloud Organization Admin**
  3. **Production Database Read/Write Access**
  4. **Bastion SSH Sudo / Root Access**
  5. **EDR / CrowdStrike Security Agent Bypass**
- **Workflow**:
  - System generates ticket (e.g. SR-10295) in `Pending Security & Management Review`.
  - Requires Dual Sign-Off: Direct Department VP + Information Security Officer (CISO On-Call).
  - Temporary Just-in-Time (JIT) access granted for a maximum duration of 4 hours with audit session logging.
