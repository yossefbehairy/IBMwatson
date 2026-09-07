# IT Navigator — Context-Aware IT Support Orchestrator
### Production Technical Documentation & Build Runbook
**Platform:** IBM watsonx Orchestrate  
**Cloud Instance:** `https://api.eu-gb.watson-orchestrate.cloud.ibm.com/instances/44e00af6-23d2-4ec1-b06f-506d97dd2083`  
**Workspace:** `00000000-0000-0000-0000-000000000001` (Global Workspace)  
**Status:** Deployed & Verified (58/58 Automated Tests Passing)

---

## 1. Executive Summary & Vision

In enterprise IT support, employees typically struggle with manual self-triage: determining whether an issue is a knowledge base self-fix, a service request for software/hardware, an operational break-fix incident, or an urgent escalation. Guesswork causes misrouted tickets, lost employee productivity, and delayed resolution for critical outages.

**IT Navigator** resolves this through an intelligent, context-aware orchestration layer built natively on **IBM watsonx Orchestrate**. An employee describes their issue in natural language. IT Navigator extracts intent and affected systems, enriches the request with real-time enterprise context (service health, criticality tier, open incident clusters, user entitlements), runs the situation through a **modular deterministic policy engine**, and delegates execution to specialized collaborator agents across three pathways:

1. **Resolve**: Safe, self-service remediation via verified IT runbooks.
2. **Request**: Catalog item provisioning with automated eligibility checks and Human-in-the-Loop (HITL) approval gates.
3. **Escalate**: Incident management with automated deduplication against active outages, deterministic P1–P4 matrix computation, and gated Major Incident candidate escalation.

---

## 2. Core Architectural Boundary: The Three Decision Layers

A central architectural requirement is the strict boundary between probabilistic AI reasoning and deterministic enterprise governance:

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

| Layer | Responsibility | Implementation |
|---|---|---|
| **AI Reasoning** | Intent understanding, natural language conversation, signal extraction | Primary Agent (`watsonx/meta-llama/llama-3-3-70b-instruct`) |
| **Deterministic Rules** | Pathway routing, Priority matrix, SLAs, Access eligibility, Major Incident criteria | 4 Pure Python Modules (`src/policy_engine/`) & OpenAPI 3.0 endpoints |
| **Human-in-the-Loop** | Privileged access grants, Security exceptions, Major Incident declaration | Watson Orchestrate `requires_approval: true` action gates |

> **Hard Governance Invariant:** The LLM is **never** permitted to finalize priority, grant access, or declare major incidents. It proposes structured signals to the Policy Engine, follows the policy outcome strictly, and explains the resulting `reasoning_code` to the user in plain language.

---

## 3. Live Deployment Summary on IBM watsonx Orchestrate

All components have been deployed, configured, and bound on the live IBM watsonx Orchestrate instance.

### 3.1 Registered Agents (4 Agents)

| Agent Name | Live Cloud ID | Role | Foundation Model | Reasoning Style |
|---|---|---|---|---|
| **`it_navigator_primary`** | `bfca1c2f-bc1d-4ffd-abae-6237674c1992` | Primary Orchestrator & Conversational Router | `watsonx/meta-llama/llama-3-3-70b-instruct` | `react_intrinsic` |
| **`it_knowledge_agent`** | `1a4d4d83-c6bf-43e3-8b46-d42adf7def8e` | Resolve Specialist (Knowledge Base Search) | `watsonx/ibm/granite-3-8b-instruct` | `react_intrinsic` |
| **`service_request_agent`** | `ab57857f-dd95-4d88-9486-06a5dcad262a` | Request Specialist (Catalog & Provisioning) | `watsonx/ibm/granite-3-8b-instruct` | `react_intrinsic` |
| **`incident_management_agent`** | `62aef221-7a71-4a23-a88a-95538c739cb2` | Escalate Specialist (Incident & Outage Merging) | `watsonx/ibm/granite-3-8b-instruct` | `react_intrinsic` |

### 3.2 Registered Tools (12 Tools)

| Tool Name | Live Cloud Tool ID | Category | Type / Binding |
|---|---|---|---|
| **`get_context`** | `6e9e0a25-27b6-41bb-805a-7c5affea998b` | Context Layer | Python (`src.connectors.context_provider`) |
| **`classify_security_risk`** | `93a3b610-d200-4fae-a45d-92037a869b4f` | Security Classifier | Python (`src.security.security_classifier`) |
| **`resolve_pathway`** | `b72377b1-b55d-444e-bc6a-72da436dd845` | Policy Engine | Python (`src.policy_engine.pathway_resolver`) |
| **`evaluate_priority`** | `6bfe8c7f-d6b3-43d5-9b94-517e1940b67a` | Policy Engine | Python (`src.policy_engine.priority_engine`) |
| **`evaluate_major_incident`** | `f3c8cd14-2280-4dd9-9eea-ef515bd7b190` | Policy Engine | Python (`src.policy_engine.major_incident_engine`) |
| **`evaluate_eligibility_and_approval`** | `62184430-dbd0-4f77-beaa-b6a6a64ec27b` | Policy Engine | Python (`src.policy_engine.eligibility_engine`) |
| **`check_similar_incidents`** | `0d1b9700-9377-4169-a8d8-5d1cb27d951a` | ITSM Connector | Python / OpenAPI (`check_similar_incidents`) |
| **`search_knowledge_base`** | `96572a42-d840-4094-ac10-999a7a4979e9` | KB Connector | Python / Vector Search (`search_knowledge_base`) |
| **`create_or_update_incident`** | `f96b1386-a067-4a0d-b03f-c999706fa715` | ITSM Connector | Python / OpenAPI (`create_or_update_incident`) |
| **`create_service_request`** | `36a4b06e-89c0-43f6-8ad5-d96643188913` | IAM Connector | Python / OpenAPI (`create_service_request`) |
| **`grant_access`** | `8a7f855f-2d2c-4f0c-b49c-db104e5dc85d` | IAM Connector | HITL Gated Action (`grant_access`) |
| **`declare_major_incident`** | `c6f3ebae-e243-41d3-9d3a-252c57d0e3ef` | ITSM Connector | HITL Gated Action (`declare_major_incident`) |

---

## 4. Codebase Directory & File Structure

```
c:/Users/RePack/Desktop/agent/
├── config.json                               # Instance URL & IBM Cloud API Key
├── requirements.txt                          # Python dependencies (fastapi, uvicorn, pydantic, pytest)
├── run.bat                                   # Interactive Windows batch console launcher
├── watson_orchestrate_client.py              # Extended client with agent & tool CRUD
├── README.md                                 # Full Master Technical Documentation (this file)
│
├── docs/
│   └── ARCHITECTURE.md                       # Architectural specification manual
│
├── src/
│   ├── __init__.py
│   ├── models/                               # Strongly-typed Pydantic V2 schemas
│   │   ├── __init__.py
│   │   ├── context.py                        # SituationContext, UserContext, IssueContext, etc.
│   │   └── decisions.py                      # PathwayDecision, PriorityDecision, EligibilityDecision
│   │
│   ├── policy_engine/                        # Modular Deterministic Policy Engine
│   │   ├── __init__.py
│   │   ├── pathway_resolver.py               # Section 7.1: Resolve vs Request vs Escalate vs Clarify
│   │   ├── priority_engine.py                # Section 7.2 & 7.5: P1-P4 Matrix & SLAs
│   │   ├── major_incident_engine.py          # Section 7.3: Major Incident candidacy evaluation
│   │   └── eligibility_engine.py             # Section 7.4: Access catalog & HITL approval triggers
│   │
│   ├── security/                             # Two-Layer Security Detection
│   │   ├── __init__.py
│   │   └── security_classifier.py            # Fast regex floor + Semantic implicit detector
│   │
│   ├── connectors/                           # Stateful Enterprise Mocks & Context Provider
│   │   ├── __init__.py
│   │   ├── context_provider.py               # Section 6: Unified Situation Object assembler
│   │   ├── mock_itsm.py                      # ServiceNow/Jira incident deduplication & outage merging
│   │   ├── mock_iam.py                       # User directory, catalog requests, access provisioning
│   │   └── mock_kb.py                        # Verified IT runbooks with safety tagging
│   │
│   ├── api/                                  # OpenAPI 3.0 REST Microservice (Appendix A)
│   │   ├── __init__.py
│   │   └── policy_server.py                  # FastAPI server hosting policy & context endpoints
│   │
│   └── orchestrator/                         # Agent Management & Deployment Pipeline
│       ├── __init__.py
│       ├── tool_registry.py                  # Tool definitions for all 12 tools
│       ├── agent_definitions.py              # ADK schemas, guidelines, instructions for 4 agents
│       ├── deployer.py                       # Automated deployment script to Watson Orchestrate
│       └── runner.py                         # End-to-end conversation simulator
│
└── tests/                                    # Automated Test Suite & Release Gate (58 tests)
    ├── __init__.py
    ├── test_policy_engine.py                 # 20 exhaustive unit tests for 4 policy modules
    ├── test_security_classifier.py           # 24 tests for explicit & implicit security detection
    ├── test_golden_dataset.py                # 9 Section 12.1 Golden Dataset categories
    └── test_watson_integration.py            # 5 live integration tests with Watson Orchestrate
```

---

## 5. Detailed Component Specifications

### 5.1 Context Signals Model (`src/models/context.py`)
Implements the single unified "Situation Object" described in Section 6:
```json
{
  "user": {
    "id": "u12345",
    "name": "Sarah Connor",
    "department": "Sales",
    "role": "Account Executive",
    "location": "Cairo",
    "manager_id": "u10021"
  },
  "issue": {
    "raw_text": "I can't access Salesforce and I have a client meeting in 20 minutes.",
    "detected_intent": "access_login_issue",
    "affected_service": "Salesforce",
    "stated_urgency": "high",
    "time_sensitivity_minutes": 20,
    "prior_resolve_attempted": false
  },
  "service_context": {
    "business_criticality": "Tier 1",
    "current_health_status": "degraded",
    "known_open_incidents": 1,
    "similar_reports_last_hour": 3
  },
  "policy_context": {
    "user_access_level": "standard",
    "existing_entitlements": ["Salesforce - Standard User", "Slack - Standard"],
    "requires_privileged_flag": false
  },
  "security_signal": {
    "flag": false,
    "confidence": 0.05,
    "category": null
  },
  "kb_match_confidence": 0.0,
  "kb_match_is_safe": false,
  "kb_match_article_id": null
}
```

---

### 5.2 Deterministic Policy Engine (`src/policy_engine/`)

#### 1. Pathway Resolver (`pathway_resolver.py`)
Enforces routing precedence:
- **Rule 1 (Security Override)**: `security_signal.flag = true` $\rightarrow$ **Escalate** (`reasoning_code: SECURITY_SIGNAL_ACTIVE`).
- **Rule 2 (Prior Attempt Failed)**: `prior_resolve_attempted = true` $\rightarrow$ **Escalate** (`reasoning_code: PRIOR_RESOLVE_FAILED`).
- **Rule 3 (Active Outage / Degradation Cluster)**: Service health is `degraded`/`down` or similar reports $\ge 2$ $\rightarrow$ **Escalate** (`reasoning_code: SERVICE_OUTAGE_OR_CLUSTER`).
- **Rule 4 (Safe Self-Fix Available)**: KB match confidence $\ge 0.70$ and fix is classified safe $\rightarrow$ **Resolve** (`reasoning_code: SAFE_KB_MATCH_AVAILABLE`).
- **Rule 5 (Provisioning Intent)**: Requesting new software, hardware, or access $\rightarrow$ **Request** (`reasoning_code: PROVISIONING_REQUEST_DETECTED`).
- **Rule 6 (Ambiguity Guardrail)**: Query lacks service or error details $\rightarrow$ **Clarify** (`reasoning_code: AMBIGUOUS_SIGNAL_NEEDS_CLARIFICATION`, `missing_signal: affected_service_or_error_details`).
- **Rule 7 (Unserviceable Break/Fix)**: Default to **Escalate** (`reasoning_code: UNSERVICEABLE_BREAK_FIX`).

#### 2. Priority Matrix & SLAs (`priority_engine.py`)
Computes priority and SLA deterministically:

| Business Criticality | Blast Radius (Users) | Stated Urgency | Priority | Response SLA | Resolution SLA | Reasoning Code |
|---|---|---|---|---|---|---|
| **Tier 1** | Multiple ($\ge 2$) | High / Critical | **P1** | 15 minutes (0.25h) | 4 hours | `TIER1_MULTIPLE_USERS_HIGH_URGENCY` |
| **Tier 1** | Single ($< 2$) | High / Critical | **P2** | 1 hour | 8 hours | `TIER1_SINGLE_USER_HIGH_URGENCY` |
| **Tier 1** | Any | Low / Medium | **P3** | 4 hours | 48 hours (2 days) | `TIER1_LOW_MEDIUM_URGENCY` |
| **Tier 2** | Multiple ($\ge 2$) | High / Critical | **P2** | 1 hour | 8 hours | `TIER2_MULTIPLE_USERS_HIGH_URGENCY` |
| **Tier 2** | Single ($< 2$) | Any | **P3** | 4 hours | 48 hours (2 days) | `TIER2_SINGLE_USER` |
| **Tier 3** | Any | Any | **P4** | 24 hours (1 day) | 120 hours (5 days) | `TIER3_INTERNAL_SERVICE` |

#### 3. Major Incident Engine (`major_incident_engine.py`)
Flags `major_incident_candidate = true` when any condition is met:
- **Criterion 1**: `security_signal.flag = true` (`SECURITY_INCIDENT_ESCALATION`).
- **Criterion 2**: Service health is `down` on Tier 1 or Tier 2 (`CRITICAL_SERVICE_COMPLETE_OUTAGE`).
- **Criterion 3**: Tier 1 service with affected reports $\ge 3$ or degraded with cluster $\ge 2$ (`TIER1_HIGH_IMPACT_CLUSTER`).
- **Criterion 4**: Executive / Board / Media visibility mentioned (`EXECUTIVE_VISIBILITY_IMPACT`).
*Governance Rule:* Candidate never auto-declares; alerts the Major Incident Manager (MIM) on-call for human declaration.

#### 4. Access Eligibility & Approval Matrix (`eligibility_engine.py`)
- **Privileged Access / Security Exceptions**: Root access, firewall exception, temporary local admin $\rightarrow$ `is_privileged = true`, `approval_required = true`, `approver_role = "IT Security"` (Mandatory HITL).
- **Hardware Requests**: Laptop, monitor, keyboard $\rightarrow$ `approval_required = true`, `approver_role = "Line manager"`.
- **Pre-Approved Role Entitlements**: Standard tools pre-approved for role (e.g., Salesforce for Account Executive, GitHub for Software Engineer) $\rightarrow$ `approval_required = false` (Auto-provision).
- **Non-Standard Software**: Specialized licenses outside baseline $\rightarrow$ `approval_required = true`, `approver_role = "Line manager"`.

---

### 5.3 Two-Layer Security Classifier (`src/security/security_classifier.py`)

A critical requirement of the build specification is that security detection must not rely solely on security jargon:

1. **Layer 1: Fast Regex Guardrail (Floor)**
   Matches explicit terms: `hacked`, `phishing`, `ransomware`, `breach`, `unauthorized access`, `credential leak`, `compromised account`.
   - Returns: `flag = true`, `confidence = 1.0`.

2. **Layer 2: Semantic Implicit Pattern Detector (Fail-Safe Biased)**
   Detects implicit threats without security vocabulary:
   - **Cross-user data leakage**: *"I can see a colleague's client records that I shouldn't have access to"*, *"seeing another employee's salary and bonus details"*.
   - **Session confusion / Hijacking**: *"the app logged me in as someone else when I refreshed"*, *"profile displays a different user's name and email"*.
   - **MFA anomalies / Credential stuffing**: *"received a 2FA prompt on my authenticator app but I didn't try to log in"*.
   - **Social engineering / harvesting**: *"someone contacted me asking for my one-time verification code"*, *"popup asking for my Windows password"*.
   - **Unexplained privilege changes**: *"my account suddenly has administrator rights and delete buttons"*.
   - **PII / Financial spills**: *"customer export file contains unencrypted credit card numbers"*.
   - **Fail-Safe Bias**: Any ambiguity defaults to `flag = true`. A false positive causes an Escalate route; a false negative risks exposing breached credentials or confidential data.

---

### 5.4 OpenAPI 3.0 Policy Microservice (`src/api/policy_server.py`)
Conforms to Appendix A OpenAPI specification:
- `POST /resolve-pathway` (`resolve_pathway`): Consumes `SituationContext`, returns `PathwayDecision`.
- `POST /evaluate-priority` (`evaluate_priority`): Consumes `SituationContext`, returns `PriorityDecision`.
- `POST /evaluate-major-incident` (`evaluate_major_incident`): Consumes `SituationContext`, returns `MajorIncidentDecision`.
- `POST /evaluate-eligibility-approval` (`evaluate_eligibility_and_approval`): Consumes `SituationContext`, returns `EligibilityDecision`.
- `POST /classify-security` (`classify_security_risk`): Consumes text, returns `SecuritySignal`.
- `POST /get-context` (`get_context`): Assembles unified `SituationContext`.
- `GET /health`: Healthcheck endpoint.

---

## 6. End-to-End Walkthrough Execution (Section 10 Scenario)

### The Employee Query
> *"I can't access Salesforce and I have a client meeting in 20 minutes."*

### Step-by-Step Execution Trace:
1. **Signal Extraction (`get_context`)**:
   - User: `Sarah Connor` (`u12345`, Account Executive in Sales).
   - Affected Service: `Salesforce` (CMDB lookup: Criticality = `Tier 1`).
   - Service Health: `degraded` (3 similar reports in the last hour).
   - Stated Urgency: `high` (time sensitivity: `20 minutes`).
   - Security Classifier (`classify_security_risk`): `flag = false` (reads as service degradation, not account takeover).

2. **Policy Evaluation (`resolve_pathway`)**:
   - Detects wider outage cluster on Tier 1 service (`SERVICE_OUTAGE_OR_CLUSTER`).
   - Unconditionally selects **`escalate`**.

3. **Priority & Major Incident Computation**:
   - `evaluate_priority`: Tier 1 $\times$ Multiple Users $\times$ High Urgency $\rightarrow$ **`P1`** (Response SLA: 15 min, Resolution SLA: 4 hours).
   - `evaluate_major_incident`: Tier 1 degraded cluster $\rightarrow$ **`major_incident_candidate = true`**.

4. **Incident Management Agent Action**:
   - Checks ITSM for open tickets on Salesforce.
   - Finds existing active incident **`INC0004521`** (*"Salesforce login degradation and intermittent session timeouts"*).
   - Merges Sarah Connor into `affected_users` rather than opening a duplicate ticket.
   - Appends meeting deadline note for the on-call engineer: `[Client deadline in 20 min]`.
   - Alerts on-call Major Incident Manager for declaration review.

5. **Natural Language Response to Employee**:
   > *"This looks like a wider Salesforce issue affecting several team members right now. I've attached you to the existing incident (**INC0004521**, Priority: **P1**, response SLA within 0 hr). I have highlighted your meeting deadline in 20 minutes as an urgent note for the responding engineer. I'll notify you as soon as updates are posted."*

---

## 7. Automated Test Suite & Release Gate Verification

The complete regression test suite comprises 58 automated tests across four test files, all passing:

```powershell
& "C:\Users\RePack\AppData\Local\Programs\Python\Python311\python.exe" -m pytest tests/ -v
```

### Test Suite Breakdown (58 Passed):
1. **`tests/test_golden_dataset.py` (9 Tests)**:
   - Category 1: Clear Resolve (VPN reconnect self-service fix offered) $\rightarrow$ **PASSED**
   - Category 2: Clear Request (Figma access request routed to catalog) $\rightarrow$ **PASSED**
   - Category 3: Clear Escalate (Expense app 500 error break-fix ticket) $\rightarrow$ **PASSED**
   - Category 4: Ambiguous / Borderline (*"it's being weird"* triggers `clarify`) $\rightarrow$ **PASSED**
   - Category 5: Security — Explicit (*"account got hacked"* fast-path escalate) $\rightarrow$ **PASSED**
   - Category 6: Security — Implicit (*"see a colleague's client records"*, ZERO TOLERANCE RELEASE GATE) $\rightarrow$ **PASSED**
   - Category 7: Conflicting Context (Urgency inflation on Tier 3 printer held to P4) $\rightarrow$ **PASSED**
   - Category 8: Gaming Attempts (Urgency wording on monitor request does not bypass manager approval) $\rightarrow$ **PASSED**
   - Category 9: Duplicate Incident Merge (Salesforce outage merged into `INC0004521`) $\rightarrow$ **PASSED**

2. **`tests/test_policy_engine.py` (20 Tests)**:
   - Exhaustive coverage across all cells of the Section 7.2 Priority Matrix, SLA computations, Major Incident criteria triggers, and Role entitlement approval matrices $\rightarrow$ **100% PASSED**.

3. **`tests/test_security_classifier.py` (24 Tests)**:
   - 6 explicit keyword threat tests $\rightarrow$ **PASSED**
   - 10 implicit security threat tests (zero security vocabulary) $\rightarrow$ **PASSED**
   - 8 benign break-fix and request negative controls (no false positives) $\rightarrow$ **PASSED**

4. **`tests/test_watson_integration.py` (5 Tests)**:
   - Live IBM Cloud IAM token exchange $\rightarrow$ **PASSED**
   - Live agent and workspace retrieval $\rightarrow$ **PASSED**
   - 12 tool schemas structure verification $\rightarrow$ **PASSED**
   - 4 agent definitions structure verification $\rightarrow$ **PASSED**
   - Deployment dry-run validation $\rightarrow$ **PASSED**

---

## 8. Operator Runbook & Launcher Guide

### Using `run.bat`
To run the interactive launcher, double-click `run.bat` in the project root:

```
=====================================================================
          IT Navigator - Context-Aware IT Support Orchestrator
                   Platform: IBM watsonx Orchestrate
=====================================================================

  [1] Test Watson Orchestrate API Connection and List Live Agents
  [2] Run Deterministic Policy Engine and Security Unit Tests
  [3] Run Golden Dataset Evaluation Suite (Section 12 Release Gate)
  [4] Run Section 10 Walkthrough Scenario (Salesforce Outage)
  [5] Interactive Query Console (Test any custom employee problem)
  [6] Start OpenAPI Policy Engine Microservice (FastAPI on port 8000)
  [7] Deploy / Sync Agents and Tools to Watson Orchestrate
  [8] Exit

=====================================================================
Select an option (1-8):
```

### CLI Command Reference
- **Run all automated tests**:
  ```powershell
  & "C:\Users\RePack\AppData\Local\Programs\Python\Python311\python.exe" -m pytest tests/ -v
  ```
- **Run interactive simulation on a custom query**:
  ```powershell
  & "C:\Users\RePack\AppData\Local\Programs\Python\Python311\python.exe" src/orchestrator/runner.py --query "I need elevated admin access to production databases"
  ```
- **Start OpenAPI REST Server**:
  ```powershell
  & "C:\Users\RePack\AppData\Local\Programs\Python\Python311\python.exe" -m uvicorn src.api.policy_server:app --reload --port 8000
  ```
  *(Visit `http://127.0.0.1:8000/docs` to view Swagger UI).*
- **Synchronize / Re-Deploy to Watson Orchestrate**:
  ```powershell
  & "C:\Users\RePack\AppData\Local\Programs\Python\Python311\python.exe" src/orchestrator/deployer.py
  ```
