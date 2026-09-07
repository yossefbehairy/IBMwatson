# IT Navigator — Context-Aware IT Support Orchestrator
### IBM watsonx Orchestrate Build Specification & Architecture Manual

## 1. Overview & Architecture

The **IT Navigator** replaces self-triage guesswork by serving as the primary context-aware IT support orchestrator. An employee describes their issue in natural language; IT Navigator extracts structured context, consults a modular deterministic policy engine, and delegates to specialist collaborator agents across three pathways:

1. **Resolve**: Safe self-service runbook remediation via the IT Knowledge Base.
2. **Request**: Catalog item provisioning with automated eligibility checks and Human-in-the-Loop (HITL) approval gates for privileged access.
3. **Escalate**: Incident management with automated deduplication against active outages, deterministic P1–P4 matrix computation, and gated Major Incident candidate escalation.

```
                         ┌─────────────────────────────┐
                         │   Employee (chat / Slack /   │
                         │   Teams / portal)            │
                         └───────────────┬─────────────┘
                                         │ natural language
                                         ▼
                         ┌─────────────────────────────┐
                         │      IT Navigator            │
                         │      (Primary Agent)         │
                         │  - intent & context extract  │
                         │  - route: Resolve/Request/   │
                         │    Escalate                  │
                         └───┬───────────┬──────────┬───┘
                             │           │          │
                 ┌───────────┘           │          └────────────┐
                 ▼                       ▼                       ▼
     ┌───────────────────┐   ┌────────────────────┐   ┌───────────────────────┐
     │ Knowledge Agent     │   │ Service Request     │   │ Incident Management    │
     │ (Resolve)           │   │ Agent (Request)      │   │ Agent (Escalate)       │
     │ - KB search          │   │ - catalog lookup     │   │ - create/update ticket │
     │ - guided fix          │   │ - eligibility check  │   │ - major-incident flag  │
     └─────────┬───────────┘   └─────────┬────────────┘   └───────────┬────────────┘
               │                          │                            │
               ▼                          ▼                            ▼
     ┌────────────────────────────────────────────────────────────────────────┐
     │                   Shared Tools & Context Layer                          │
     │  - Context Tool (user, department, app health, similar-incident count)  │
     │  - Security Classifier (semantic security-risk detection — not just     │
     │    keyword matching; feeds security_signal into context)                │
     │  - Policy Engine — modular: Pathway Resolver / Priority / Eligibility &  │
     │    Approval / Major Incident                                            │
     │  - Enterprise connectors: ITSM, IAM, CMDB, Knowledge Base Runbooks     │
     └────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
                 ┌───────────────────────────┐
                 │  Human-in-the-Loop layer   │
                 │  (privileged access,       │
                 │   security exceptions,     │
                 │   major incident sign-off) │
                 └───────────────────────────┘
```

---

## 2. Decision Layers & Hard Boundaries

| Layer | Component | Implementation |
|---|---|---|
| **AI Reasoning** | Intent understanding & entity extraction | Primary Agent (`watsonx/meta-llama/llama-3-3-70b-instruct`) |
| **Deterministic Rules** | Pathway, Priority, SLAs, Eligibility, Approvals, Major Incident candidate criteria | 4 Pure Python Modules (`src/policy_engine/`) & OpenAPI endpoints |
| **Human-in-the-Loop** | Privileged access grants, Security exceptions, Major Incident declaration | Watson Orchestrate `requires_approval: true` action gates |

---

## 3. Registered Agents in Watson Orchestrate

| Agent Name | Role | Model | Tools |
|---|---|---|---|
| `it_navigator_primary` | Primary Orchestrator | `watsonx/meta-llama/llama-3-3-70b-instruct` | `get_context`, `classify_security_risk`, `resolve_pathway` |
| `it_knowledge_agent` | Resolve Specialist | `watsonx/ibm/granite-3-8b-instruct` | `search_knowledge_base` |
| `service_request_agent` | Request Specialist | `watsonx/ibm/granite-3-8b-instruct` | `evaluate_eligibility_and_approval`, `create_service_request`, `grant_access` |
| `incident_management_agent` | Escalate Specialist | `watsonx/ibm/granite-3-8b-instruct` | `check_similar_incidents`, `evaluate_priority`, `evaluate_major_incident`, `create_or_update_incident`, `declare_major_incident` |

---

## 4. Deterministic Policy Engine Modules

### 4.1 Pathway Resolver (`src/policy_engine/pathway_resolver.py`)
- `security_signal.flag = true` $\rightarrow$ **Escalate** (Unconditional override).
- `prior_resolve_attempted = true` $\rightarrow$ **Escalate** (Never trap user in repeated self-fix).
- Service degraded or outage cluster $\ge 2$ $\rightarrow$ **Escalate** (Bypasses individual self-service during system incidents).
- High confidence ($\ge 0.70$) & safe KB match $\rightarrow$ **Resolve**.
- Provisioning / catalog intent $\rightarrow$ **Request**.
- Break/fix with no safe KB fix $\rightarrow$ **Escalate**.
- Missing required signals $\rightarrow$ **Clarify**.

### 4.2 Priority Matrix (`src/policy_engine/priority_engine.py`)
| Business Criticality | Users Affected | Stated Urgency | Priority | Response SLA | Resolution SLA |
|---|---|---|---|---|---|
| Tier 1 | Multiple | High | **P1** | 15 min | 4 hours |
| Tier 1 | Single | High | **P2** | 1 hour | 8 hours |
| Tier 1 | Any | Low/Medium | **P3** | 4 hours | 48 hours (2 days) |
| Tier 2 | Multiple | High | **P2** | 1 hour | 8 hours |
| Tier 2 | Single | Any | **P3** | 4 hours | 48 hours (2 days) |
| Tier 3 | Any | Any | **P4** | 24 hours (1 day) | 120 hours (5 days) |

### 4.3 Major Incident Engine (`src/policy_engine/major_incident_engine.py`)
Flags `major_incident_candidate = true` when:
- Criticality = Tier 1 and affected users $\ge 3$ (or degraded with cluster).
- Active security signal (`security_signal.flag = true`).
- Complete outage (`down`) on Tier 1 or Tier 2.
- Executive/Media visibility flag.
*Invariant*: Never auto-declares; alerts Major Incident Manager (MIM) for human declaration.

### 4.4 Access Eligibility & Approval Matrix (`src/policy_engine/eligibility_engine.py`)
- Standard software pre-approved for role $\rightarrow$ Auto-provision (`approval_required = false`).
- Non-standard software or hardware $\rightarrow$ Line Manager approval required.
- Elevated/Privileged access (root, admin, firewall) $\rightarrow$ Mandatory Human-in-the-Loop (`IT Security` approver).

---

## 5. Security Classifier (`src/security/security_classifier.py`)
- **Layer 1: Fast Regex Floor**: Catches explicit keywords (`hacked`, `phishing`, `breach`, `unauthorized`, `ransomware`, `credential leak`).
- **Layer 2: Semantic Pattern Detector**: Detects implicit data leaks without security vocabulary (*"seeing another employee's salary"*, *"logged me in as someone else"*, *"export has credit cards"*, *"received 2FA code unexpectedly"*).
- **Fail-Safe Bias**: Any ambiguity flags `security_signal.flag = true` to prevent data leakage from routing to self-service.

---

## 6. How to Run & Verify

1. **Interactive Menu**: Run `run.bat` to launch the interactive management menu.
2. **Execute Full Test Suite**:
   ```powershell
   & "C:\Users\RePack\AppData\Local\Programs\Python\Python311\python.exe" -m pytest tests/ -v
   ```
3. **Run Section 10 Walkthrough**:
   ```powershell
   & "C:\Users\RePack\AppData\Local\Programs\Python\Python311\python.exe" src/orchestrator/runner.py --query "I can't access Salesforce and I have a client meeting in 20 minutes."
   ```
4. **Start OpenAPI Server**:
   ```powershell
   & "C:\Users\RePack\AppData\Local\Programs\Python\Python311\python.exe" -m uvicorn src.api.policy_server:app --port 8000
   ```
   Interactive Swagger UI available at `http://127.0.0.1:8000/docs`.
