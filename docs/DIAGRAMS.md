# NEXUS — Architecture Diagrams

## 1. Overall System Architecture

```mermaid
graph TB
    subgraph "React 14 Command Center (Next.js)"
        UI_INTEL["🔍 Intelligence\n(Silo Buster, GIS)"]
        UI_OPS["⚙️ Operational\n(Tasks, Assignment)"]
        UI_GOV["📋 Governance\n(Approval, Escalation)"]
        UI_NOTIFY["🔔 Notifications\n(Inbox, Digests)"]
        UI_EXEC["📊 Executive\n(Dashboard, KPIs)"]
        UI_AUDIT["🔐 Audit & Compliance\n(Ledger, Risk)"]
    end

    subgraph "FastAPI Backend"
        AUTH["Auth Engine\n(JWT + RBAC)"]
        ANALYTICS["Analytics Engine\n(Entity Res, DBSCAN, CUSUM)"]
        SILO["Silo Buster\n(Neo4j Traversals + XAI)"]
        TASKS["Task DAG Engine\n(Dependencies + SLA)"]
        ASSIGN["Assignment Engine\n(Workload + Jurisdiction)"]
        APPROVAL["Approval Engine\n(Multi-Tier + Delegation)"]
        ESCALATION["Escalation Engine\n(SLA Breach + Delegation)"]
        NOTIFY["Notification Hub\n(Priority + Digest + Threading)"]
        COMMAND["Command Center\n(Supervisor + Executive)"]
        WORKSPACE["Investigation Workspace\n(Cases + Evidence)"]
        AUDIT["Immutable Audit Ledger\n(SHA-256 Hash Chaining)"]
        COMPLIANCE["Compliance Engine\n(20 Rules + Risk 0-100)"]
        EVENTS["EventDispatcher\n(Pub/Sub Backbone)"]
    end

    subgraph "Data Layer"
        PG[("PostgreSQL 15\nRelational Records")]
        NEO[("Neo4j 5.12\nGraph Intelligence")]
        SQLITE[("SQLite :memory:\nTest Isolation")]
    end

    UI_INTEL --> AUTH
    UI_OPS --> AUTH
    UI_GOV --> AUTH
    UI_NOTIFY --> AUTH
    UI_EXEC --> AUTH
    UI_AUDIT --> AUTH

    AUTH --> ANALYTICS & SILO & TASKS & ASSIGN
    AUTH --> APPROVAL & ESCALATION & NOTIFY & COMMAND
    AUTH --> WORKSPACE & AUDIT & COMPLIANCE

    TASKS --> EVENTS
    ASSIGN --> EVENTS
    APPROVAL --> EVENTS
    ESCALATION --> EVENTS
    NOTIFY --> EVENTS

    EVENTS --> AUDIT
    EVENTS --> COMPLIANCE

    ANALYTICS --> PG
    SILO --> NEO
    TASKS --> PG
    ASSIGN --> PG
    APPROVAL --> PG
    ESCALATION --> PG
    NOTIFY --> PG
    AUDIT --> PG
    COMPLIANCE --> PG
```

---

## 2. Event-Driven Backbone

```mermaid
sequenceDiagram
    participant Feature as Feature Service<br/>(Task/Approval/etc.)
    participant ED as EventDispatcher
    participant AES as AuditEventSubscriber
    participant CEL as ComplianceEventListener
    participant DB as PostgreSQL

    Feature->>ED: publish_sync(BaseEvent, db)
    ED->>AES: consume_event(event, db)
    AES->>DB: AuditLedgerRecord (SHA-256 chained)
    AES-->>ED: ack
    ED->>CEL: consume_event(event, db)
    CEL->>CEL: RuleEngine.evaluate(rules, event)
    CEL->>DB: ComplianceViolationRecord (if rule fired)
    CEL-->>ED: ack
    ED-->>Feature: sync complete
```

---

## 3. Investigation Lifecycle

```mermaid
stateDiagram-v2
    [*] --> InvestigationCreated : Commander creates case
    InvestigationCreated --> TasksGenerated : DAG Engine generates tasks
    TasksGenerated --> WorkloadAnalyzed : Assignment Engine scores officers
    WorkloadAnalyzed --> SupervisorReview : Recommendation presented
    SupervisorReview --> OfficerAssigned : Supervisor approves assignment
    SupervisorReview --> Reassigned : Supervisor overrides with rationale
    OfficerAssigned --> NotificationDispatched : Notification Hub alerts officer
    NotificationDispatched --> WorkInProgress : Officer acknowledges
    WorkInProgress --> SLAWarning : SLA < 20% remaining
    SLAWarning --> SLABreached : SLA exceeded
    SLABreached --> Escalated : Escalation Engine triggers
    Escalated --> Delegated : Supervisor delegates upward
    WorkInProgress --> EvidenceSubmitted : Officer submits evidence
    EvidenceSubmitted --> ApprovalRequested : Requires supervisor approval
    ApprovalRequested --> ApprovalGranted : Multi-tier review complete
    ApprovalGranted --> ExecutiveDashboardUpdated : KPI refreshed
    ExecutiveDashboardUpdated --> AuditEntryGenerated : SHA-256 chained record
    AuditEntryGenerated --> ComplianceChecked : 20 rules evaluated
    ComplianceChecked --> [*]
```

---

## 4. Approval Lifecycle

```mermaid
sequenceDiagram
    participant Officer as Investigating Officer
    participant AP as Approval Engine
    participant SUP as Supervisor
    participant ACP as ACP
    participant ED as EventDispatcher
    participant NH as Notification Hub
    participant AL as Audit Ledger

    Officer->>AP: submit_approval(request)
    AP->>AP: Validate policy rules
    AP->>NH: Notify supervisor
    NH->>SUP: Approval request notification

    SUP->>AP: action(APPROVE/REJECT, comments)
    AP->>AP: Check if multi-tier required
    alt Single-tier sufficient
        AP->>ED: APPROVAL_APPROVED event
        ED->>AL: Audit entry (SHA-256 chained)
        AP->>NH: Notify officer of outcome
    else Multi-tier required (ACP needed)
        AP->>NH: Forward to ACP
        NH->>ACP: Escalated approval request
        ACP->>AP: action(APPROVE)
        AP->>ED: APPROVAL_APPROVED event
        ED->>AL: Audit entry (SHA-256 chained)
    end

    alt Delegation (Supervisor unavailable)
        AP->>AP: Check delegation rules & expiry
        AP->>ACP: Auto-delegate with audit record
    end
```

---

## 5. SHA-256 Audit Hash Chain

```mermaid
graph LR
    G["Genesis Block\nprev_hash = 0x000...000\nsequence = 0"] --> R1
    R1["Record #1\nevent: TASK_CREATED\nhash = SHA256(prev+payload+seq)\nsequence = 1"] --> R2
    R2["Record #2\nevent: APPROVAL_SUBMITTED\nhash = SHA256(prev+payload+seq)\nsequence = 2"] --> R3
    R3["Record #3\nevent: ASSIGNMENT_CREATED\nhash = SHA256(prev+payload+seq)\nsequence = 3"] --> RN
    RN["Record #N\n...\nsequence = N"]

    style G fill:#1a1a2e,color:#e94560
    style R1 fill:#16213e,color:#0f3460
    style R2 fill:#16213e,color:#0f3460
    style R3 fill:#16213e,color:#0f3460
```

**Tamper Detection**: Any modification to any record changes its hash, breaking the chain for all subsequent records. The integrity sweep verifies every `prev_hash → hash` link in O(N).
